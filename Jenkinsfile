pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    triggers {
        githubPush()
        pollSCM('H/2 * * * *')
    }

    environment {
        PYTHONUNBUFFERED = '1'
        JENKINS_NODE_COOKIE = 'dontKillMe'
        BUILD_ID = 'dontKillMe'

        DB_HOST = '127.0.0.1'
        DB_PORT = '3306'
        DB_NAME = 'ecommerce_test'
        DB_USER = 'root'
        DB_PASSWORD = ''

        API_BASE_URL = 'http://127.0.0.1:8000'
        HEADLESS = 'true'

        // Python installation confirmed on this Jenkins machine
        PYTHON_EXE = 'C:\\Users\\NEELGAGAN B R\\AppData\\Local\\Programs\\Python\\Python314\\python.exe'
    }

    stages {

        stage('1. Checkout') {
            steps {
                echo '========================================'
                echo '1. CHECKOUT'
                echo '========================================'

                checkout scm
            }
        }

        stage('2. Verify Python') {
            steps {
                echo '========================================'
                echo '2. VERIFY PYTHON'
                echo '========================================'

                bat '''
                    echo Python executable:
                    "%PYTHON_EXE%"

                    echo.
                    echo Python version:
                    "%PYTHON_EXE%" --version

                    echo.
                    echo Pip version:
                    "%PYTHON_EXE%" -m pip --version
                '''
            }
        }

        stage('3. Create Python Environment') {
            steps {
                echo '========================================'
                echo '3. CREATE PYTHON VIRTUAL ENVIRONMENT'
                echo '========================================'

                bat '''
                    if exist venv (
                        echo Existing virtual environment found.
                    ) else (
                        echo Creating virtual environment...
                        "%PYTHON_EXE%" -m venv venv
                    )

                    echo.
                    echo Verifying virtual environment...

                    venv\\Scripts\\python.exe --version
                    venv\\Scripts\\python.exe -m pip --version
                '''
            }
        }

        stage('4. Install Dependencies') {
            steps {
                echo '========================================'
                echo '4. INSTALL DEPENDENCIES'
                echo '========================================'

                bat '''
                    echo Upgrading pip...

                    venv\\Scripts\\python.exe -m pip install --upgrade pip

                    echo.
                    echo Installing requirements...

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
                echo '5. PREPARE REPORT DIRECTORY'
                echo '========================================'

                bat '''
                    if not exist reports mkdir reports

                    echo Reports directory is ready.
                '''
            }
        }

        stage('6. Verify MySQL') {
            steps {
                echo '========================================'
                echo '6. VERIFY MYSQL'
                echo '========================================'

                bat '''
                    venv\\Scripts\\python.exe -c "import mysql.connector; conn = mysql.connector.connect(host='%DB_HOST%', port=%DB_PORT%, user='%DB_USER%', password='%DB_PASSWORD%'); print('MySQL Server Online'); print('Host: %DB_HOST%'); print('Port: %DB_PORT%'); conn.close()"
                '''
            }
        }

        stage('7. Setup Database') {
            steps {
                echo '========================================'
                echo '7. SETUP DATABASE'
                echo '========================================'

                bat '''
                    venv\\Scripts\\python.exe database\\db_setup.py init
                '''
            }
        }

        stage('8. Start Application') {
            steps {
                echo '========================================'
                echo '8. START FASTAPI APPLICATION'
                echo '========================================'

                bat '''
                    echo Cleaning any previous FastAPI instances...
                    taskkill /F /IM uvicorn.exe /T >nul 2>&1 || (exit /b 0)

                    echo Starting FastAPI...
                    set JENKINS_NODE_COOKIE=dontKillMe
                    set BUILD_ID=dontKillMe
                    start "" /B venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

                    echo Waiting for FastAPI application to initialize...
                    venv\\Scripts\\python.exe -c "import time; time.sleep(3)"

                    echo Checking FastAPI health endpoint...
                    venv\\Scripts\\python.exe -c "import time, requests; [time.sleep(1) for _ in range(15) if requests.get('http://127.0.0.1:8000/health').status_code != 200]; r = requests.get('http://127.0.0.1:8000/health', timeout=5); print('HTTP Status:', r.status_code); assert r.status_code == 200, 'FastAPI application failed to start'"

                    echo.
                    echo FastAPI application started successfully.
                '''
            }
        }

        stage('9. Run Database Tests') {
            steps {
                echo '========================================'
                echo '9. RUN DATABASE TESTS'
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
                echo '10. RUN API TESTS'
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
                echo '11. RUN UI TESTS'
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
                echo '12. RUN INTEGRATION TESTS'
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
                echo '13. GENERATE CONSOLIDATED REPORTS'
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
            echo 'ARCHIVING REPORTS'
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

            echo 'All test stages completed successfully.'
        }

        failure {
            echo '========================================'
            echo 'PIPELINE FAILED'
            echo '========================================'

            echo 'Check the failed stage in the Jenkins console.'
        }

        cleanup {
            echo '========================================'
            echo 'CLEANUP'
            echo '========================================'

            bat '''
                taskkill /F /IM uvicorn.exe /T >nul 2>&1
                exit /b 0
            '''
        }
    }
}
