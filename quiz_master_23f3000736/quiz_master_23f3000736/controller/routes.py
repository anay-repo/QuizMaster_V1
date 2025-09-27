from app import app
from flask import render_template, session, redirect, url_for, flash, request
from controller.models import *
from controller.database import db
from datetime import datetime

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        return render_template('login.html')

    if request.method == "POST":
        email = request.form.get('email', None)
        password = request.form.get('password', None)

        # Data validation
        if not email or not password:
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()
        if not user:
            return render_template('login.html')

        if user.password != password:
            return render_template('login.html')

        session['user_email'] = user.email

        if user.password == '1234567890':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "GET":
        return render_template('register.html')

    if request.method == "POST":   
        username = request.form.get('username', None)
        email = request.form.get('email', None)
        password = request.form.get('password', None)
        qualification = request.form.get('qualification', None)
        fullname = request.form.get('fullname', None)
        dob_str = request.form.get('dob', None)
        
        if not username or not email or not password or not dob_str or not qualification:
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            return render_template('register.html')

        dob = datetime.strptime(dob_str, '%Y-%m-%d').date()

        user = User(
            username=username,
            email=email,
            password=password,
            dob=dob,
            qualification=qualification,
            fullname=fullname,
        )

        db.session.add(user)
        db.session.commit()
        flash('Chapter updated successfully!', 'success')

        flash('User registered successfully')
        return redirect(url_for('login'))
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(email=session['user_email']).first()

    if not user or user.password != '1234567890':
        return redirect(url_for('login'))
    
    # Search functionality
    search_query = request.args.get('search', '')
    
    if search_query:
        users = User.query.filter(User.username.like(f'%{search_query}%')).all()
        subjects = Subject.query.filter(Subject.name.like(f'%{search_query}%')).all()
        quizzes = Quiz.query.filter(Quiz.date_of_quiz.like(f'%{search_query}%')).all()
        questions = Question.query.filter(Question.question_statement.like(f'%{search_query}%')).all()
        chapters = Chapter.query.filter(Chapter.name.like(f'%{search_query}%')).all()
    else:
        users = User.query.all()
        subjects = Subject.query.all()
        quizzes = Quiz.query.all()
        questions = Question.query.all()
        chapters = Chapter.query.all()
    
    subject_scores = []
    subject_attempts = []
    
    for subject in subjects:

        subject_chapters = Chapter.query.filter_by(subject_id=subject.id).all()
        chapter_ids = [chapter.id for chapter in subject_chapters]
        subject_quizzes = Quiz.query.filter(Quiz.chapter_id.in_(chapter_ids)).all() if chapter_ids else []
        quiz_ids = [quiz.id for quiz in subject_quizzes]
        scores = Score.query.filter(Score.quiz_id.in_(quiz_ids)).all() if quiz_ids else []
        total_score = sum([score.score for score in scores]) if scores else 0
        avg_score = total_score / len(scores) if scores else 0
        attempts = len(scores)
        
        subject_scores.append({
            'subject_name': subject.name,
            'avg_score': round(avg_score, 2),
            'total_score': total_score
        })
        
        subject_attempts.append({
            'subject_name': subject.name,
            'attempts': attempts
        })
    
    return render_template('admin_dashboard.html', users=users, subjects=subjects, quizzes=quizzes, questions=questions, subject_scores=subject_scores, subject_attempts=subject_attempts, search_query=search_query, chapters=chapters)

@app.route('/create_subject', methods=['GET'])
def create_subject_form():
    return render_template('create_subject.html')

@app.route('/create_subject', methods=['POST'])
def create_subject():
    subject_id = request.form.get('subjectId')
    subject_name = request.form.get('subjectName')
    subject_description = request.form.get('subjectDescription')
    
    if not subject_name:
        return redirect(url_for('create_subject_form'))
    
    new_subject = Subject(
            name=subject_name,
            description=subject_description,
        )
    db.session.add(new_subject)
    db.session.commit()
    flash('Subject created successfully')
    return redirect(url_for('admin_dashboard'))


@app.route('/edit_subject/<int:id>', methods=['GET'])
def edit_subject_form(id):
    subject = Subject.query.filter_by(id=id).first()
    if not subject:
        flash('Subject not found')
        return redirect(url_for('admin_dashboard'))
    return render_template('edit_subject.html', subject=subject)

@app.route('/edit_subject/<int:id>', methods=['POST'])
def edit_subject(id):
    subject = Subject.query.filter_by(id=id).first()
    if not subject:
        flash('Subject not found')
        return redirect(url_for('admin_dashboard'))
    subject.name = request.form.get('subjectName')
    subject.description = request.form.get('subjectDescription')
    
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.route('/delete_subject/<int:id>')
def delete_subject(id):
    subject = Subject.query.filter_by(id=id).first()
    
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/edit_subject')
def edit_subject_list():
    subjects = Subject.query.all()
    return render_template('edit_subject_list.html', subjects=subjects)


@app.route('/delete_subject')
def delete_subject_list():
    subjects = Subject.query.all()
    return render_template('delete_subject_list.html', subjects=subjects)

@app.route('/create_chapter', methods=['GET', 'POST'])
def create_chapter():
    subjects = Subject.query.all()
    
    if request.method == 'GET':
        return render_template('create_chapter.html', subjects=subjects)

    if request.method == 'POST':
        chapter_name = request.form.get('chapterName')
        subject_id = request.form.get('subjectId')
        description = request.form.get('chapterDescription')
        
        if not chapter_name or not subject_id:
            flash('All fields are required')
            return render_template('create_chapter.html', subjects=subjects)
        
        new_chapter = Chapter(
                name=chapter_name,
                subject_id=subject_id,
                Description=description
            )
        
        db.session.add(new_chapter)
        db.session.commit()
        flash('Chapter created successfully')
        return redirect(url_for('admin_dashboard'))

@app.route('/edit_chapter', methods=['GET'])
def edit_chapter_list():
    chapters = Chapter.query.all()
    return render_template('edit_chapter_list.html', chapters=chapters)

@app.route('/edit_chapter/<int:id>', methods=['GET', 'POST'])
def edit_chapter(id):
    chapter = Chapter.query.filter_by(id=id).first()
    
    if request.method == 'GET':
        subjects = Subject.query.all()
        return render_template('edit_chapter.html', chapter=chapter, subjects=subjects)
    
    if request.method == "POST":
        chapter.name = request.form.get('chapterName')
        chapter.subject_id = request.form.get('subjectId')
        chapter.description = request.form.get('chapterDescription')
        
        db.session.commit()
        flash('Chapter updated successfully')
        return redirect(url_for('admin_dashboard'))

@app.route('/delete_chapter', methods=['GET'])
def delete_chapter_list():
    chapters = Chapter.query.all()
    return render_template('delete_chapter_list.html', chapters=chapters)

@app.route('/delete_chapter/<int:id>', methods=['GET'])
def delete_chapter(id):
    chapter = Chapter.query.filter_by(id=id).first()
    if not chapter:
        flash('Chapter not found')
        return redirect(url_for('admin_dashboard'))
    
    db.session.delete(chapter)
    db.session.commit()
    flash('Chapter deleted successfully')
    return redirect(url_for('admin_dashboard'))

@app.route('/create_quiz', methods=['GET', 'POST'])
def create_quiz():
    if request.method == 'GET':
        chapters = Chapter.query.all()
        return render_template('create_quiz.html', chapters=chapters)

    if request.method == 'POST':
        chapter_id = request.form.get('chapterId')
        date_of_quiz = request.form.get('quizDate')
        time_duration = request.form.get('quizDuration')

        if not chapter_id or not date_of_quiz or not time_duration:
            flash('All fields are required')
            chapters = Chapter.query.all()
            return render_template('create_quiz.html', chapters=chapters)
        
        new_quiz = Quiz(
            chapter_id=chapter_id,
            date_of_quiz=date_of_quiz,
            time_duration=time_duration,
        )
        db.session.add(new_quiz)
        db.session.commit()
        flash('Quiz created successfully')
        return redirect(url_for('admin_dashboard'))

@app.route('/edit_quiz', methods=['GET'])
def edit_quiz_list():
    quizzes = Quiz.query.all()
    return render_template('edit_quiz_list.html', quizzes=quizzes)

@app.route('/edit_quiz/<int:id>', methods=['GET', 'POST'])
def edit_quiz(id):
    quiz = Quiz.query.get_or_404(id)
    
    if request.method == 'GET':
        chapters = Chapter.query.all()
        return render_template('edit_quiz.html', quiz=quiz, chapters=chapters)
    
    if request.method == 'POST':
        quiz.chapter_id = request.form.get('chapterId')
        quiz.date_of_quiz = request.form.get('quizDate')
        quiz.time_duration = request.form.get('quizDuration')
        
        db.session.commit()
        flash('Quiz updated successfully')
        return redirect(url_for('admin_dashboard'))

@app.route('/delete_quiz', methods=['GET'])
def delete_quiz_list():
    quizzes = Quiz.query.all()
    return render_template('delete_quiz_list.html', quizzes=quizzes)

@app.route('/delete_quiz/<int:id>', methods=['GET'])
def delete_quiz(id):
     quiz = Quiz.query.filter_by(id=id).first()
     if not quiz:
         flash('Quiz not found')
         return redirect(url_for('admin_dashboard'))
     questions = Question.query.filter_by(quiz_id=id).all()
     for question in questions:
         db.session.delete(question)
     scores = Score.query.filter_by(quiz_id=id).all()
     for score in scores:
         db.session.delete(score)
         
     db.session.delete(quiz)
     db.session.commit()
     flash('Quiz deleted successfully')
     return redirect(url_for('admin_dashboard'))
    

@app.route('/add_questions/<int:quiz_id>', methods=['GET', 'POST'])
def add_questions(quiz_id):
    quiz = Quiz.query.filter_by(id=quiz_id).first()
    
    if request.method == 'GET':
        questions = Question.query.filter_by(quiz_id=quiz_id).all()
        return render_template('add_questions.html', quiz=quiz, questions=questions)

    if request.method == 'POST':
        question_statement = request.form.get('questionStatement')
        option1 = request.form.get('option1')
        option2 = request.form.get('option2')
        option3 = request.form.get('option3')
        option4 = request.form.get('option4')
        correct_option = request.form.get('correctOption')
        
        if not question_statement or not option1 or not option2 or not option3 or not option4 or not correct_option:
            flash('All fields are required', 'error')
            return render_template('add_questions.html', quiz=quiz, questions=questions)
        
        new_question = Question(
            quiz_id=quiz_id,
            question_statement=question_statement,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_option=correct_option,
        )
        db.session.add(new_question)
        db.session.commit()
        flash('Question added successfully')
        return redirect(url_for('add_questions', quiz_id=quiz_id))

@app.route('/edit_question/<int:id>', methods=['GET', 'POST'])
def edit_question(id):
    question = Question.query.filter_by(id=id).first()
    if not question:
        flash('Question not found')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'GET':
        return render_template('edit_question.html', question=question)

    if request.method == 'POST':
        question.question_statement = request.form.get('questionStatement')
        question.option1 = request.form.get('option1')
        question.option2 = request.form.get('option2')
        question.option3 = request.form.get('option3')
        question.option4 = request.form.get('option4')
        question.correct_option = request.form.get('correctOption')
        
        db.session.commit()
        flash('Question updated successfully')
        return redirect(url_for('add_questions', quiz_id=question.quiz_id))

@app.route('/delete_question/<int:id>', methods=['GET'])
def delete_question(id):
    question = Question.query.filter_by(id=id).first()
    if not question:
        flash('Question not found')
        return redirect(url_for('admin_dashboard'))
    quiz_id = question.quiz_id
    
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully')
    return redirect(url_for('add_questions', quiz_id=quiz_id))

#USER MANAGEMENT

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_email' not in session:
        flash("Please login to access this page")
        return redirect(url_for('login'))
    user = User.query.filter_by(email=session['user_email']).first()
    all_subjects = Subject.query.all()
    available_subjects = []
    subject_stats = []
    
    for subject in all_subjects:
        subject_chapters = Chapter.query.filter_by(subject_id=subject.id).all()
        subject_quizzes = []
        
        total_available_quizzes = 0
        
        for chapter in subject_chapters:
            quizzes = Quiz.query.filter_by(chapter_id=chapter.id).all()
            for quiz in quizzes:
                questions = Question.query.filter_by(quiz_id=quiz.id).all()
                if questions:
                    total_available_quizzes += 1
                    subject_quizzes.append({
                        'quiz': quiz,
                        'chapter': chapter,
                        'total_questions': len(questions)
                    })
        attempts_for_subject = db.session.query(Score).join(
            Quiz, Score.quiz_id == Quiz.id
        ).join(
            Chapter, Quiz.chapter_id == Chapter.id
        ).filter(
            Chapter.subject_id == subject.id,
            Score.user_id == user.id
        ).all()
        
        subject_stats.append({
            'name': subject.name,
            'available_quizzes': total_available_quizzes,
            'attempted_quizzes': len(attempts_for_subject)
        })
        
        if subject_quizzes:
            available_subjects.append({
                'subject': subject,
                'quizzes': subject_quizzes
            })
    
    past_attempts = Score.query.filter_by(user_id=user.id).order_by(
        Score.id.desc()
    ).all()

    return render_template('user_dashboard.html', user=user, available_subjects=available_subjects, past_attempts=past_attempts, subject_stats=subject_stats)


@app.route('/start_quiz/<int:quiz_id>')
def start_quiz(quiz_id):
    user = User.query.filter_by(email=session['user_email']).first()
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    return render_template('start_quiz.html', user=user, quiz=quiz, questions=questions)

@app.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
def submit_quiz(quiz_id):
    user = User.query.filter_by(email=session['user_email']).first()
    quiz = Quiz.query.filter_by(id=quiz_id).first()
    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    user_answers = {}
    questions_data = []
    
    for question in questions:
        user_answer = request.form.get(f"question_{question.id}")
        if user_answer:
            user_answers[question.id] = int(user_answer)
        
        question_dict = {
            'id': question.id,
            'question_statement': question.question_statement,
            'option1': question.option1,
            'option2': question.option2,
            'option3': question.option3,
            'option4': question.option4,
            'correct_option': question.correct_option
        }
        questions_data.append(question_dict)
    
    correct_count = sum(1 for question in questions 
                        if user_answers.get(question.id) == question.correct_option)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    score_record = Score(
        user_id=user.id,
        quiz_id=quiz.id,
        score=correct_count,
        total_scored=len(questions),
        time_stamp_of_attempt=timestamp
    )
    
    db.session.add(score_record)
    db.session.commit()
    
    return render_template('quiz_results.html', user=user, quiz=quiz, questions=questions_data, user_answers=user_answers, total_questions=len(questions), correct_answers=correct_count)