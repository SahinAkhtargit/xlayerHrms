frappe.pages['employee-holiday-vie'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Employee Holiday Viewer',
        single_column: true
    });

    // Get employee linked to current user
    frappe.call('frappe.client.get_list', {
        doctype: 'Employee',
        filters: { user_id: frappe.session.user },
        fields: ['name']
    }).then(emp_res => {
        if (!emp_res.message || emp_res.message.length === 0) {
            page.body.innerHTML = `<p>No Employee record found for ${frappe.session.user}</p>`;
            return;
        }

        const employee = emp_res.message[0].name;

        // Call your API
        frappe.call({
            method: 'rchrms.holidayAndBirthdayApi.get_holiday_list',
            args: { employee },
            callback: function(r) {
                if (!r.message || !r.message.status) {
                    page.body.innerHTML = `<p>${r.message.message}</p>`;
                    return;
                }

                // Filter only non-weekly-off holidays
                const holidays = r.message.data.filter(h => h.weekly_off === 0);

                if (holidays.length === 0) {
                    page.body.innerHTML = `<p>No holidays found (excluding weekly offs).</p>`;
                    return;
                }

                let html = `<table class="table table-bordered">
                    <thead><tr><th>Date</th><th>Description</th></tr></thead><tbody>`;

                holidays.forEach(h => {
                    html += `<tr>
                        <td>${frappe.datetime.str_to_user(h.holiday_date)}</td>
                        <td>${frappe.utils.strip_html(h.description)}</td>
                    </tr>`;
                });

                html += `</tbody></table>`;
                page.body.innerHTML = html;
            }
        });
    });
};

