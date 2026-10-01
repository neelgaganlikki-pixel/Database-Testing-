pipeline {
    agent any

    environment {
        PYTHONUNBUFFERED = '1'
        DB_HOST = '127.0.0.1'
        DB_PORT = '3306'
        DB_NAME = 'ecommerce_test'
        DB_USER = 'root'
        DB_PASSWORD = ''
        API_BASE_URL = 'http://127.0.0.1:8000'
        HEADLESS = 'true'
    }

    stages {
        stage('1. Checkout') {
            steps {
                echo 'Checking out source repository...'
                checkout scm
            }
        }

        stage('2. Create Python Environment') {
            steps {
                echo 'Setting up Python virtual environment...'
                bat '''
                    if not exist venv (
                        python -m venv venv
                    )
                '''
            }
        }

        stage('3. Install Dependencies') {
            steps {
                echo 'Installing required testing dependencies...'
                bat '''
                    call venv\\Scripts\\activate.bat
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    playwright install chromium
                '''
            }
        }

        stage('4. Verify MySQL') {
            steps {
                echo 'Verifying MySQL service connection...'
                bat '''
                    call venv\\Scripts\\activate.bat
                    python -c "import mysql.connector; conn = mysql.connector.connect(host='%DB_HOST%', port=%DB_PORT%, user='%DB_USER%', password='%DB_PASSWORD%'); print('MySQL Server Online'); conn.close()"
                '''
            }
        }

        stage('5. Setup Database') {
            steps {
                echo 'Creating schema and seeding test data...'
                bat '''
                    call venv\\Scripts\\activate.bat
                    python database/db_setup.py init
                '''
            }
        }

        stage('6. Start Application') {
            steps {
                echo 'Starting FastAPI application daemon...'
                bat '''
                    call venv\\Scripts\\activate.bat
                    start /b uvicorn app.main:app --host 127.0.0.1 --port 8000
                    timeout /t 5 /nobreak >nul
                    python -c "import requests; r = requests.get('http://127.0.0.1:8000/health'); assert r.status_code == 200, 'App failed to start'"
                '''
            }
        }

        stage('7. Run Database Tests') {
            steps {
                echo 'Executing Database Test Suite...'
                bat '''
                    call venv\\Scripts\\activate.bat
                    pytest -m database -v --junitxml=reports/junit-database.xml
                '''
            }
        }

        stage('8. Run API Tests') {
            steps {
                echo 'Executing REST API Test Suite...'
                bat '''
                    call venv\\Scripts\\activate.bat
                    pytest -m api -v --junitxml=reports/junit-api.xml
                '''
            }
        }

        stage('9. Run UI Tests') {
            steps {
                echo 'Executing Playwright UI Test Suite...'
                bat '''
                    call venv\\Scripts\\activate.bat
                    pytest -m ui -v --junitxml=reports/junit-ui.xml
                '''
            }
        }

        stage('10. Run Integration Tests') {
            steps {
                echo 'Executing End-to-End & Integration Suite...'
                bat '''
                    call venv\\Scripts\\activate.bat
                    pytest -m integration -v --junitxml=reports/junit-integration.xml
                '''
            }
        }

        stage('11. Generate Reports') {
            steps {
                echo 'Generating consolidated HTML and JUnit reports...'
                bat '''
                    call venv\\Scripts\\activate.bat
                    pytest -v --html=reports/pytest-report.html --self-contained-html --junitxml=reports/junit-results.xml
                '''
            }
        }
    }

    post {
        always {
            echo 'Archiving test artifacts and reports...'
            junit testResults: 'reports/*.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
        }
        success {
            echo 'All test stages completed successfully!'
        }
        failure {
            echo 'Pipeline failed due to test assertion or build errors.'
        }
        cleanup {
            echo 'Tearing down test environment...'
            bat '''
                taskkill /F /IM uvicorn.exe /T 2>nul || exit 0
            '''
        }
    }
}

