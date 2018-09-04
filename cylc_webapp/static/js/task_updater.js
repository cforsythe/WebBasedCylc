var CURRENT_STATE= -1
var TABLE_COLUMNS = ['name','state', 'host','latest_message', 'batch_sys_name', 'submit_method_id', 'submitted_time_string', 'started_time_string', 'finished_time_string', 'mean_elapsed_time']
var TABLE_NAME = 'JobBody'
// regex plugin

function isInt(time){
    return Number(time) === time && time % 1 === 0;
}

function isFloat(time){
    return Number(time) === time && time % 1 !== 0;
}

function isValidDuration(time){
    return isInt(time) || isFloat(time) 
}

function loadBarCreated(row){
    return $(this).find("#finished-time-string .loader").length != 0
}   

function generateLoaderHtml(time, value, overtime, estFinish){
    var htmlLoader = `<td >
                        <div class="outline">
                            <div class='progress-bar progress-bar-striped ${overtime} active' role='progressbar'
                            aria-valuenow=${value} aria-valuemin='0' aria-valuemax='100' 
                            style=width:${value}%>
                                ${estFinish}
                            </div>
                        </div>
                      </td>`;
    return htmlLoader
}

function estimateFinishTime(startTime, secondsToCompletion){
    var estFinish = startTime;
    estFinish.setSeconds(startTime.getSeconds() + secondsToCompletion);
    estFinish = estFinish.toISOString() + "?";
    return estFinish;
}


function addNewBars(){
    $("#JobBody tr").each(function(){
        var secondsToCompletion = Number($(this).find("#mean-elapsed-time").textContent);
        var loadBar = $(this).find("#finished-time-string");
        var state = $(this).find("#state").textContent;
        if(isValidDuration(secondsToCompletion) && !loadBarCreated(this) && state == "running"){
            dateString = $(this).find("#started-time-string").textContent
            var startTime = new Date(dateString)
            var currentTime = Date.now()
            estFinish = estimateFinishTime(startTime, secondsToCompletion)
            var progress = (currentTime - startTime)/1000
            var loaderVal = (progress/secondsToCompletion*100);
            if(loaderVal > 100){
                var overtime = "progress-bar-over";
                loaderVal = 100
            }
            loadBar.replaceWith(generateLoaderHtml(secondsToCompletion, loaderVal, overtime, estFinish))
        }
    })
}
function isEmptyObject(obj){
    for(var key in obj){
        if(obj.hasOwnProperty(key)){
            return false;
        }
    }
    return true;
}
function sortTable(tableName, n){
    var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
    table = document.getElementById(tableName);
    switching = true;
    // Set the sorting direction to ascending:
    dir = "asc"; 
    /* Make a loop that will continue until
    no switching has been done: */
    while (switching) {
        // Start by saying: no switching is done:
        switching = false;
        rows = table.rows;
        /* Loop through all table rows (except the
        first, which contains table headers): */
        for (i = 1; i < (rows.length - 1); i++) {
           // Start by saying there should be no switching:
            shouldSwitch = false;
            /* Get the two elements you want to compare,
            one from current row and one from the next: */
            x = rows[i].getElementsByTagName("TD")[n];
            y = rows[i + 1].getElementsByTagName("TD")[n];
            /* Check if the two rows should switch place,
            based on the direction, asc or desc: */
            if(n != 0){
                if (dir == "asc") {
                    if (x.textContent.toLowerCase() > y.textContent.toLowerCase()) {
                    // If so, mark as a switch and break the loop:
                    shouldSwitch = true;
                    break;
                    }
                } 
                else if (dir == "desc") {
                    if (x.textContent.toLowerCase() < y.textContent.toLowerCase()) {
                    // If so, mark as a switch and break the loop:
                    shouldSwitch = true;
                    break;
                    }
                }
            }
            else{
                if(rows[i].id > rows[i + 1].id){
                    shouldSwitch = true;
                    break;
                }
            }
        }
        if (shouldSwitch) {
            /* If a switch has been marked, make the switch
            and mark that a switch has been done: */
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
      // Each time a switch is done, increase this count by 1:
            switchcount ++; 
        }
        else {
            /* If no switching has been done AND the direction is "asc",
            set the direction to "desc" and run the while loop again. */
            if (switchcount == 0 && dir == "asc") {
                dir = "desc";
                switching = true;
            }
        }
    }
}
function buildNestedId(row, td){
    row = $.escapeSelector(row)
    return "#" + row + " #" + td 
}
function idNotFound(id){
    return $(id).length === 0
}
function isString(str){
    return typeof str === 'string'
}
function deleteRows(jobs){
    for(job in jobs){
        $("#" + $.escapeSelector(jobs[job])).remove();
    }
}
function updateRow(job, id){
    for(const [attr, data] of Object.entries(job)){
        fullId = buildNestedId(id, attr);
        if(!idNotFound(fullId)){
           $(fullId + " #text").text(data) 
        }
    }
}
function updateJobs(jobs){
    if('$delete' in jobs){
        deleteRows(jobs['$delete'])
        delete jobs['$delete']
    }
    if('$replace' in jobs){
        populateJobs(jobs['$replace']);
    }
    else{
        for(const [jobName, data] of Object.entries(jobs)){
            if(idNotFound("#" + $.escapeSelector(jobName))){
                flatJob = reframeJob(data, TABLE_COLUMNS) 
                appendRow(TABLE_NAME, flatJob, jobName, TABLE_COLUMNS)
            }
            else{
                updateRow(data, jobName)
            }
        }
    }
    sortTable(TABLE_NAME, 0)
    setStates(TABLE_NAME)
}
function populateJobs(jobs){
    $("#" + TABLE_NAME).empty()
    for(const [jobName, data] of Object.entries(jobs)){
        flatJob = reframeJob(data, TABLE_COLUMNS) 
        appendRow(TABLE_NAME, flatJob, jobName, TABLE_COLUMNS)
    }
}
function reframeJob(job, attributes){
    var reframedJob = [] 
    for(var i = 0; i < attributes.length; i++){
        if(attributes[i] in job && job[attributes[i]] != ""){
            reframedJob.push(job[attributes[i]])
        }
        else{
            reframedJob.push("*")
        }
    }
    return reframedJob
}
function appendRow(table, job, id, columns){
    var tbl = document.getElementById(table), row = tbl.insertRow(tbl.rows.length);
    row.setAttribute('id', id);
    for(var i = 0; i < columns.length; i++){
        var procPath = id.split(".");
        if(procPath.length < 2){
            var processName = "root";
        }
        else{
            var processName = procPath[procPath.length - 1];
        }
        createCell(row.insertCell(i), job[i], columns[i], processName);
    }
}
function buildName(text, processName){
    var state = document.createElement("div")
    var margin = document.createElement("div")
    var div = document.createElement("div")
    state.setAttribute('class', 'circle')
    state.setAttribute('id', 'state_circle')
    margin.setAttribute('id', 'spacing')
    margin.setAttribute('class', 'child_margins')
    div.appendChild(state)
    div.appendChild(margin)
    if(JSON.parse(sessionStorage.getItem('childCounts'))[processName] > 0){
        var arrow = document.createElement("div")
        arrow.setAttribute('class', 'arrow');
        arrow.setAttribute('id', 'arrow');
        div.appendChild(arrow);
    }
    div.appendChild(text);
    return div;
}
function createCell(cell, text, columnName, processName){
    var txt = document.createTextNode(text);
    var procNameSpan = document.createElement('span');
    procNameSpan.setAttribute('id', 'text')
    procNameSpan.appendChild(txt)
    cell.setAttribute('id', columnName) 
    if(columnName == "name"){
        div = buildName(procNameSpan, processName)
        cell.appendChild(div)
    }
    else{
        cell.appendChild(procNameSpan);
    }
}
