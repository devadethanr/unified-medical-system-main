$(document).ready(function() {
    $('.patient-view-modal').on('shown.bs.modal', function() {
       console.log('Modal shown, initializing DataTable...');
       if (!$.fn.DataTable.isDataTable('#patientsTable')) {
          $('#patientsTable').DataTable({
             "ajax": {
                "url": "{{ url_for('admin.api_patients') }}",
                "dataSrc": ""
             },
             "columns": [
                { "data": "umsId" },
                { "data": "createdAt" },
                { "data": "updatedAt" },
                { "data": "dateOfBirth" },
                { "data": "user_info.name" },
                { "data": "user_info.email" },
                { "data": "gender" },
                {
                   "data": null,
                   "render": function(data, type, row) {
                      return '<a href="/edit_patient/' + row.umsId + '" class="btn btn-primary">Edit</a>';
                   }
                }
             ]
          });
       }
    });
 });




 $('.doctor-view-modal').on('shown.bs.modal', function() {
    console.log('Modal shown, initializing DataTable...');
    if (!$.fn.DataTable.isDataTable('#doctorsTable')) {
       $('#doctorsTable').DataTable({
          "ajax": {
             "url": "{{ url_for('admin.api_doctors') }}",
             "dataSrc": ""
          },
          "columns": [
             { "data": "umsId" },
             { "data": "createdAt" },
             { "data": "updatedAt" },
             { "data": "dateOfBirth" },
             { "data": "user_info.name" },
             { "data": "user_info.email" },
             { "data": "user.info.speciality" }
             { "data": null,
                "render": function(data, type, row) {
                   return '<a href="/edit_doctor/' + row.umsId + '" class="btn btn-primary">Edit</a>';
                }
             }
          ]
       });
    }
 });
});
</scri