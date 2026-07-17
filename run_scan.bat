@echo off
cd /d C:\InterviewPrep-Claude\job-radar
echo ===== scan started %date% %time% ===== >> logs\scan.log
"C:\Users\ankit\anaconda3\python.exe" -m radar.pipeline >> logs\scan.log 2>&1
echo ===== scan finished %date% %time% ===== >> logs\scan.log
