window.onload = function() {
    // 1. Get student info (simulated from session or URL)
    const params = new URLSearchParams(window.location.search);
    const firstName = params.get('f') || "Lorem";
    const lastName = params.get('s') || "Ipsum";
    const grade = params.get('grade') || "Grade 7";

    document.getElementById('student_name').innerText = `${firstName} ${lastName}`;
    document.getElementById('grade_level').innerText = grade;
    document.getElementById('student_id').innerText = Math.floor(Math.random() * 900000) + 100000;

    // 2. Automated Class List based on Grade Level
    const subjectsBody = document.getElementById('subjects_body');
    
    const curiculum = [
        { name: "Mathematics", section: "7-A", day: "Mon/Wed", time: "8:00 AM", room: "RM 101" },
        { name: "Science", section: "7-A", day: "Tue/Thu", time: "10:00 AM", room: "Lab 1" },
        { name: "Filipino", section: "7-A", day: "Fri", time: "1:00 PM", room: "RM 204" }
    ];

    curiculum.forEach(sub => {
        let row = `<tr>
            <td>${sub.name}</td>
            <td>${sub.section}</td>
            <td>${sub.day}</td>
            <td>${sub.time}</td>
            <td>${sub.room}</td>
        </tr>`;
        subjectsBody.innerHTML += row;
    });
};