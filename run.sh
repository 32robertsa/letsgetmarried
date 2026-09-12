while true; do
    ./mill run &
    MILL_PID=$!
    p3 web/pull_from_sheets.py
    sleep 60
    kill $MILL_PID
done
