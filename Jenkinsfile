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
                echo '========================================'
                echo 'Checking out source repository...'
                echo '========================================'

                checkout scm
            }
        }

        stage('2. Verify Python') {
            steps {
                echo '========================================'
                echo 'Verifying Python installation...'
                echo '========================================'

                bat '''
                    where python
                    python --version
                    python -m pip --version
                '''
            }
        }

        stage('3. Create Python Environment') {
            steps {
                echo '========================================'
                echo 'Creating Python virtual environment...'
                echo '========================================'

                bat '''
                    if exist venv (
                        echo Virtual environment already exists.
                    ) else (
                        echo Creating new virtual environment...
                        python -m venv venv
                    )

                    echo.
                    echo Python version inside virtual environment:
                    venv\\Scripts\\python.exe --version

                    echo.
                    echo Pip version inside virtual environment:
                    venv\\Scripts\\python.exe -m pip --version
                '''
            }
        }

        stage('4. Install Dependencies') {
            steps {
                echo '========================================'
                echo 'Installing Python dependencies...'
                echo '========================================'

                bat '''
                    venv\\Scripts\\python.exe -m pip install --upgrade pip

                    venv\\Scripts\\python.exe -m pip install -r requirements.txt

                    echo.
                    echo Installing Playwright Chromium...
                    venv\\Scripts\\python.exe -m playwright install chromium
                '''
            }
        }

        stage('5. Prepare Reports Directory') {
            steps {
                echo '========================================'
                echo 'Preparing reports directory...'
                echo '========================================'

                bat '''
                    if not exist reports mkdir reports

                    if exist reports\\*.xml (
                        del /Q reports\\*.xml
                    )

                    if exist reports\\pytest-report.html (
                        del /Q reports\\pytest-report.html
                    )

                    echo Reports directory ready.
                '''
            }
        }

        stage('6. Verify MySQL') {
            steps {
                echo '========================================'
                echo 'Verifying MySQL connection...'
                echo '========================================'

                bat '''
                    venv\\Scripts\\python.exe -c "import mysql.connector; conn = mysql.connector.connect(host='%DB_HOST%', port=%DB_PORT%, user='%DB_USER%', password='%DB_PASSWORD%'); print('MySQL Server Online'); print('Host: %DB_HOST%'); print('Port: %DB_PORT%'); conn.close()"
                '''
            }
        }

        stage('7. Setup Database') {
            steps {
                echo '========================================'
                echo 'Creating database schema and test data...'
                echo '========================================'

                bat '''
                    venv\\Scripts\\python.exe database\\db_setup.py init
                '''
            }
        }

        stage('8. Start Application') {
            steps {
                echo '========================================'
                echo 'Starting FastAPI application...'
                echo '========================================'

                bat '''
                    start "FastAPI" /B venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

                    echo Waiting for FastAPI application...
                    timeout /t 5 /nobreak >nul

                    echo Checking application health...

                    venv\\Scripts\\python.exe -c "import requests; r = requests.get('http://127.0.0.1:8000/health', timeout=15); print('API Status:', r.status_code); assert r.status_code == 200, 'FastAPI application failed to start'"

                    echo FastAPI application is running successfully.
                '''
            }
        }

        stage('9. Run Database Tests') {
            steps {
                echo '========================================'
                echo 'Running Database Tests...'
                echo '========================================'

                bat '''
                    venv\\Scripts\\python.exe -m pytest ^
                        -m database ^
                        -v ^
                        --junitxml=reports\\junit-database.xml
                '''
            }
        }

        stage('10. Run API Tests') {
            steps {
                echo '========================================'
                echo 'Running API Tests...'
                echo '========================================'

                bat '''
                    venv\\Scripts\\python.exe -m pytest ^
                        -m api ^
                        -v ^
                        --junitxml=reports\\junit-api.xml
                '''
            }
        }

        stage('11. Run UI Tests') {
            steps {
                echo '========================================'
                echo 'Running UI Tests...'
                echo '========================================'

                bat '''
                    venv\\Scripts\\python.exe -m pytest ^
                        -m ui ^
                        -v ^
                        --junitxml=reports\\junit-ui.xml
                '''
            }
        }

        stage('12. Run Integration Tests') {
            steps {
                echo '========================================'
                echo 'Running Integration Tests...'
                echo '========================================'

                bat '''
                    venv\\Scripts\\python.exe -m pytest ^
                        -m integration ^
                        -v ^
                        --junitxml=reports\\junit-integration.xml
                '''
            }
        }

        stage('13. Generate Reports') {
            steps {
                echo '========================================'
                echo 'Generating consolidated test reports...'
                echo '========================================'

                bat '''
                    venv\\Scripts\\python.exe -m pytest ^
                        -v ^
                        --html=reports\\pytest-report.html ^
                        --self-contained-html ^
                        --junitxml=reports\\junit-results.xml
                '''
            }
        }
    }

    post {

        always {
            echo '========================================'
            echo 'Archiving Test Reports and Artifacts'
            echo '========================================'

            junit(
                testResults: 'reports/*.xml',
                allowEmptyResults: true
            )

            archiveArtifacts(
                artifacts: 'reports/**',
                allowEmptyArchive: true,
                fingerprint: true
            )
        }

        success {
            echo '========================================'
            echo 'PIPELINE SUCCESS'
            echo '========================================'
            echo 'All database, API, UI and integration tests completed successfully.'
        }

        failure {
            echo '========================================'
            echo 'PIPELINE FAILED'
            echo '========================================'
            echo 'One or more pipeline stages failed.'
            echo 'Please check the Jenkins console output and test reports.'
        }

        unstable {
            echo '========================================'
            echo 'PIPELINE UNSTABLE'
            echo '========================================'
            echo 'Some tests may have failed or produced unstable results.'
        }

        cleanup {
            echo '========================================'
            echo 'Cleaning Up Test Environment'
            echo '========================================'

            bat '''
                taskkill /F /IM uvicorn.exe /T >nul 2>&1
                exit /b 0
            '''
        }
    }
}
