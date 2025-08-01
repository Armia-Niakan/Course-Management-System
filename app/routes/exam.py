from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
import datetime
from app.models.exam import Exam, Question
from app.models.submission import Submission
from app.services.exam_manager import ExamManager
from app.services.submission_manager import SubmissionManager
from app.services.course_manager import CourseManager
from app.services.user_manager import UserManager
from app.services.enrollment_manager import EnrollmentManager
from app.utils.decorators import login_required, teacher_required

exam_bp = Blueprint('exam', __name__, url_prefix='/exam')

@exam_bp.route('/exams')
@login_required
def exams_page():
    role = session['role']
    user_email = session['user_email']
    
    all_exams = list(ExamManager.load_exams().values())
    all_courses = CourseManager.load_courses()
    
    filtered_exams = []
    student_submissions = {}

    if role == 'student':
        enrollments = EnrollmentManager.get_student_enrollments(user_email)
        enrolled_course_ids = {e['course_id'] for e in enrollments}
        filtered_exams = [exam for exam in all_exams if exam.course_id in enrolled_course_ids]
        
        # Get submission status for the student
        submissions = SubmissionManager.load_submissions()
        for sub in submissions:
            if sub.student_email == user_email:
                student_submissions[sub.exam_id] = sub
                
    elif role == 'teacher':
        filtered_exams = [exam for exam in all_exams if all_courses.get(exam.course_id, {}).get('teacher') == user_email]

    elif role == 'admin':
        filtered_exams = all_exams

    # Add course name to each exam for display
    for exam in filtered_exams:
        exam.course_name = all_courses.get(exam.course_id, {}).get('name', 'Unknown Course')

    return render_template('exams.html', 
                           exams=sorted(filtered_exams, key=lambda x: x.course_name),
                           student_submissions=student_submissions,
                           username=session['username'], 
                           role=role)


@exam_bp.route('/create/<course_id>', methods=['GET', 'POST'])
@teacher_required
def create_exam(course_id):
    course = CourseManager.get_course(course_id)
    if not course or course['teacher'] != session['user_email']:
        flash("Unauthorized or course not found.", "error")
        return redirect(url_for('course.courses'))

    if request.method == 'POST':
        title = request.form.get('title')
        duration = int(request.form.get('duration_minutes', 60))
        
        questions = []
        
        question_indices = set()
        for key in request.form:
            if key.startswith('question_text_'):
                idx = key.split('_')[-1]
                question_indices.add(idx)

        q_id_counter = 0
        for idx in sorted(question_indices, key=int):
            text = request.form.get(f'question_text_{idx}')
            options = request.form.getlist(f'option_{idx}[]')
            correct_option_str = request.form.get(f'correct_option_{idx}')
            
            if not text or not options or correct_option_str is None:
                continue

            correct_option = int(correct_option_str)
            questions.append(Question(id=q_id_counter, text=text, options=options, correct_option=correct_option))
            q_id_counter += 1

        if not questions:
            flash("Cannot create an exam with no valid questions.", "error")
            return redirect(url_for('exam.create_exam', course_id=course_id))

        new_exam = Exam(id='', course_id=course_id, title=title, questions=questions, duration_minutes=duration)
        ExamManager.add_exam(new_exam)
        flash("Exam created successfully!", "success")
        return redirect(url_for('course.course_detail', course_id=course_id))

    return render_template('create_exam.html', course=course, username=session['username'], role=session['role'])

@exam_bp.route('/<exam_id>/take', methods=['GET', 'POST'])
@login_required
def take_exam(exam_id):
    exam = ExamManager.get_exam(exam_id)
    if not exam:
        flash("Exam not found.", "error")
        return redirect(url_for('course.courses'))

    if SubmissionManager.has_student_submitted(exam_id, session['user_email']):
        flash("You have already submitted this exam.", "error")
        return redirect(url_for('course.course_detail', course_id=exam.course_id))

    if request.method == 'POST':
        answers = {}
        correct_count = 0
        for q in exam.questions:
            selected_option = request.form.get(f'question_{q.id}')
            answers[str(q.id)] = selected_option
            if selected_option and int(selected_option) == q.correct_option:
                correct_count += 1
        
        score = (correct_count / len(exam.questions)) * 100 if exam.questions else 0

        submission = Submission(
            exam_id=exam_id,
            student_email=session['user_email'],
            answers=answers,
            score=round(score, 2),
            total_questions=len(exam.questions),
            submitted_at=datetime.datetime.now().isoformat()
        )
        SubmissionManager.add_submission(submission)
        flash(f"Exam submitted! Your score: {score:.2f}%", "success")
        return redirect(url_for('course.course_detail', course_id=exam.course_id))

    return render_template('take_exam.html', exam=exam.to_dict(), username=session['username'], role=session['role'])

@exam_bp.route('/<exam_id>/results')
@login_required
def exam_results(exam_id):
    exam = ExamManager.get_exam(exam_id)
    if not exam:
        flash("Exam not found.", "error")
        return redirect(url_for('course.courses'))

    course = CourseManager.get_course(exam.course_id)
    is_admin = session.get('role') == 'admin'
    is_course_teacher = course and course.get('teacher') == session.get('user_email')

    if not (is_admin or is_course_teacher):
        flash("You are not authorized to view these results.", "error")
        return redirect(url_for('course.course_detail', course_id=exam.course_id))

    submissions = SubmissionManager.get_submissions_for_exam(exam_id)
    results = []
    for sub in submissions:
        student = UserManager.get_user(sub.student_email)
        results.append({
            'student_name': student.username if student else 'Unknown',
            'student_email': sub.student_email,
            'score': sub.score,
            'submitted_at': sub.submitted_at
        })
    
    return render_template('exam_results.html', exam=exam, results=results, username=session['username'], role=session['role'])

@exam_bp.route('/<exam_id>/submission/<student_email>')
@login_required
def submission_detail(exam_id, student_email):
    submission = SubmissionManager.get_submission(exam_id, student_email)
    exam = ExamManager.get_exam(exam_id)
    student = UserManager.get_user(student_email)

    if not all([submission, exam, student]):
        flash("Data not found.", "error")
        return redirect(url_for('course.courses'))

    course = CourseManager.get_course(exam.course_id)
    is_admin = session.get('role') == 'admin'
    is_course_teacher = course and course.get('teacher') == session.get('user_email')
    
    if not (is_admin or is_course_teacher):
        flash("You are not authorized to view this submission.", "error")
        return redirect(url_for('course.course_detail', course_id=exam.course_id))
        
    return render_template('submission_detail.html', submission=submission, exam=exam, student=student, username=session['username'], role=session['role'])

@exam_bp.route('/delete/<exam_id>', methods=['POST'])
@login_required
def delete_exam(exam_id):
    exam = ExamManager.get_exam(exam_id)
    if not exam:
        flash("Exam not found.", "error")
        return redirect(request.referrer or url_for('course.courses'))

    course = CourseManager.get_course(exam.course_id)
    
    is_admin = session.get('role') == 'admin'
    is_course_teacher = course and course.get('teacher') == session.get('user_email')

    if not (is_admin or is_course_teacher):
        flash("You are not authorized to delete this exam.", "error")
        return redirect(url_for('course.course_detail', course_id=exam.course_id))

    if ExamManager.delete_exam(exam_id):
        flash(f"Exam '{exam.title}' and all its submissions have been deleted.", "success")
        current_app.logger.info(f"Exam {exam_id} deleted by {session['user_email']}")
    else:
        flash("Failed to delete the exam.", "error")

    return redirect(url_for('course.course_detail', course_id=exam.course_id))