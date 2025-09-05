frappe.pages['leave-details'].on_page_load = function (wrapper) {
    if (wrapper.initialized) return; 
    wrapper.initialized = true;

    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Employee Leave Details',
        single_column: true
    });
    let content = $(`
        <div style="padding: 20px;">
            <div style="display: flex; justify-content: flex-end; align-items: center; gap: 10px; margin-bottom: 20px;">
                <div id="employee_input" style="width: 300px;"></div>
                <button class="btn btn-primary" id="fetch_leave_btn">Fetch Leave Details</button>
            </div>
            <div class="leave-details-container"></div>
        </div>
    `).appendTo(page.body);

    let leave_container = content.find('.leave-details-container');

    // Employee field
    let employee_control = frappe.ui.form.make_control({
        df: {
            fieldtype: 'Link',
            options: 'Employee',
            fieldname: 'employee',
            placeholder: 'Select Employee',
        },
        parent: content.find('#employee_input'),
        render_input: true
    });

    // Button click
    content.find('#fetch_leave_btn').on('click', function () {
        let employee_value = employee_control.get_value();

        if (!employee_value) {
            frappe.msgprint("Please select an Employee.");
            return;
        }

        fetchLeaveDetails(employee_value);
    });

    function fetchLeaveDetails(employee_docname) {

        frappe.call({
            url: "/api/method/rchrms.employee_api.get_leave_dashboard",
            type: "GET",
            args: { employee: employee_docname },
            callback: function (r) {

                let res = r; 
                leave_container.empty();

                if (!res || !res.status || !res.data || !res.data.leave_allocation) {
                    leave_container.append(`<p style="color:red;">No data found.</p>`);
                    return;
                }

                let allocation = res.data.leave_allocation;
                let table = $(`
                    <table class="table table-bordered" style="background:white; width:100%;">
                        <thead style="background:#f1f1f1;">
                            <tr>
                                <th>Leave Type</th>
                                <th>Total</th>
                                <th>Taken</th>
                                <th>Pending</th>
                                <th>Remaining</th>
                                <th>Expired</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                `);

                Object.keys(allocation).forEach(type => {
                    let d = allocation[type];
                    let rowColor = d.remaining_leaves > 0 ? "inherit" : "#f8d7da";

                    table.find("tbody").append(`
                        <tr style="background:${rowColor};">
                            <td><b>${type}</b></td>
                            <td>${d.total_leaves}</td>
                            <td>${d.leaves_taken}</td>
                            <td>${d.leaves_pending_approval}</td>
                            <td>${d.remaining_leaves}</td>
                            <td>${d.expired_leaves}</td>
                        </tr>
                    `);
                });

                if (res.data.lwps && res.data.lwps.length > 0) {
                    res.data.lwps.forEach(lwp => {
                        table.find("tbody").append(`
                            <tr style="background:#fff3cd;">
                                <td><b>${lwp}</b></td>
                                <td colspan="5" style="text-align:center;">Leave Without Pay (Not Allocated)</td>
                            </tr>
                        `);
                    });
                }

                leave_container.append(table);
            }
        });
    }
};
