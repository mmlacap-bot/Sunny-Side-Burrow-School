document.addEventListener('DOMContentLoaded', function() {
    const gradeSelectInput = document.getElementById('id_grade_level');
    const sectionSelectInput = document.getElementById('id_section');
    const schoolYearSelectInput = document.getElementById('id_school_year');
    const scheduleContainer = document.getElementById('schedule-preview');

    if (gradeSelectInput && sectionSelectInput && schoolYearSelectInput) {
        console.log('Enrollment form controls found, setting up dynamic filtering...');
        
        // Filter sections when grade level or school year changes
        const filterSections = async () => {
            const gradeLevel = gradeSelectInput.value;
            const schoolYear = schoolYearSelectInput.value;

            console.log(`Filtering sections: gradeLevel=${gradeLevel}, schoolYear=${schoolYear}`);

            if (!gradeLevel || !schoolYear) {
                console.log('Missing grade level or school year, clearing sections');
                sectionSelectInput.innerHTML = '<option value="">---------</option>';
                if (scheduleContainer) scheduleContainer.style.display = 'none';
                return;
            }

            try {
                const url = `/api/get_sections_by_grade_level/?grade_level_id=${gradeLevel}&school_year_id=${schoolYear}`;
                console.log(`Fetching from: ${url}`);
                
                const response = await fetch(url);
                
                if (!response.ok) {
                    throw new Error(`API returned status ${response.status}`);
                }
                
                const sections = await response.json();
                console.log('Sections received:', sections);

                // Clear existing options (except the first empty one)
                sectionSelectInput.innerHTML = '<option value="">---------</option>';

                // Add new options
                sections.forEach(section => {
                    const option = document.createElement('option');
                    option.value = section.id;
                    option.textContent = section.name;
                    sectionSelectInput.appendChild(option);
                });
                
                console.log(`Added ${sections.length} sections to dropdown`);
            } catch (error) {
                console.error('Error fetching sections:', error);
                alert('Error loading sections. Please try again or contact support.');
            }
        };

        // Fetch and display schedule when section changes
        const displaySchedule = async () => {
            const sectionId = sectionSelectInput.value;
            
            if (!sectionId) {
                if (scheduleContainer) scheduleContainer.style.display = 'none';
                return;
            }

            try {
                const url = `/api/get_schedule_by_section/?section_id=${sectionId}`;
                console.log(`Fetching schedule from: ${url}`);
                
                const response = await fetch(url);
                
                if (!response.ok) {
                    throw new Error(`API returned status ${response.status}`);
                }
                
                const schedules = await response.json();
                console.log('Schedules received:', schedules);

                if (schedules.length === 0) {
                    if (scheduleContainer) scheduleContainer.innerHTML = '<p>No schedules available for this section.</p>';
                    return;
                }

                // Build schedule table
                let html = '<h4>Class Schedule for Selected Section</h4>';
                html += '<table style="width: 100%; margin-top: 1rem; border-collapse: collapse;">';
                html += '<thead><tr style="background-color: #CC0000; color: white;">';
                html += '<th style="padding: 0.75rem; text-align: left; border: 1px solid #ddd;">Subject</th>';
                html += '<th style="padding: 0.75rem; text-align: left; border: 1px solid #ddd;">Day</th>';
                html += '<th style="padding: 0.75rem; text-align: left; border: 1px solid #ddd;">Time</th>';
                html += '<th style="padding: 0.75rem; text-align: left; border: 1px solid #ddd;">Room</th>';
                html += '</tr></thead>';
                html += '<tbody>';

                schedules.forEach(schedule => {
                    const timeStart = schedule.time_start.substring(0, 5);
                    const timeEnd = schedule.time_end.substring(0, 5);
                    html += '<tr style="border-bottom: 1px solid #eee;">';
                    html += `<td style="padding: 0.75rem; border: 1px solid #ddd;">${schedule.subject__name}</td>`;
                    html += `<td style="padding: 0.75rem; border: 1px solid #ddd;">${schedule.day}</td>`;
                    html += `<td style="padding: 0.75rem; border: 1px solid #ddd;">${timeStart} - ${timeEnd}</td>`;
                    html += `<td style="padding: 0.75rem; border: 1px solid #ddd;">Room ${schedule.room}</td>`;
                    html += '</tr>';
                });

                html += '</tbody></table>';
                
                if (scheduleContainer) {
                    scheduleContainer.innerHTML = html;
                    scheduleContainer.style.display = 'block';
                }
            } catch (error) {
                console.error('Error fetching schedule:', error);
                if (scheduleContainer) {
                    scheduleContainer.innerHTML = '<p style="color: #b00020;">Error loading schedule. Please try again.</p>';
                    scheduleContainer.style.display = 'block';
                }
            }
        };

        // Add event listeners
        gradeSelectInput.addEventListener('change', filterSections);
        schoolYearSelectInput.addEventListener('change', filterSections);
        sectionSelectInput.addEventListener('change', displaySchedule);
        
        // Also trigger on page load in case values are pre-selected
        if (schoolYearSelectInput.value && gradeSelectInput.value) {
            filterSections();
            if (sectionSelectInput.value) {
                displaySchedule();
            }
        }
    } else {
        console.warn('Enrollment form controls not found. IDs expected: id_grade_level, id_section, id_school_year');
    }
});


