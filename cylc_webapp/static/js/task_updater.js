var current_state = -1
// regex plugin
jQuery.expr[':'].regex = function(elem, index, match) {
    var matchParams = match[3].split(','),
        validLabels = /^(data|css):/,
        attr = {
            method: matchParams[0].match(validLabels) ? 
                        matchParams[0].split(':')[0] : 'attr',
            property: matchParams.shift().replace(validLabels,'')
        },
        regexFlags = 'ig',
        regex = new RegExp(matchParams.join('').replace(/^\s+|\s+$/g,''), regexFlags);
    return regex.test(jQuery(elem)[attr.method](attr.property));
}

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
    return $(this).find("#t-finish .loader").length != 0
}   

function generateLoaderHtml(time, value, overtime, est_finish){
    var htmlLoader = `<td >
                        <div class="outline">
                            <div class='progress-bar progress-bar-striped ${overtime} active' role='progressbar'
                            aria-valuenow=${value} aria-valuemin='0' aria-valuemax='100' 
                            style=width:${value}%>
                                ${est_finish}
                            </div>
                        </div>
                      </td>`;
    return htmlLoader
}

function estimateFinishTime(start_time, secondsToCompletion){
    var est_finish = start_time;
    est_finish.setSeconds(start_time.getSeconds() + secondsToCompletion);
    est_finish = est_finish.toISOString() + "?";
    return est_finish;
}


function addNewBars(){
    $("#JobBody tr").each(function(){
        var secondsToCompletion = Number($(this).find("#mean-elapsed-time").html());
        var loadBar = $(this).find("#finished-time-string");
        var state = $(this).find("#state").html();
        if(isValidDuration(secondsToCompletion) && !loadBarCreated(this) && state == "running"){
            date_string = $(this).find("#started-time-string").html()
            var start_time = new Date(date_string)
            var current_time = Date.now()
            est_finish = estimateFinishTime(start_time, secondsToCompletion)
            var progress = (current_time - start_time)/1000
            var loaderVal = (progress/secondsToCompletion*100);
            if(loaderVal > 100){
                var overtime = "progress-bar-over";
                loaderVal = 100
            }
            loadBar.replaceWith(generateLoaderHtml(secondsToCompletion, loaderVal, overtime, est_finish))
        }
    })
}
function populate_jobs(jobs){
    table_name = "JobBody"
    $("#" + table_name).empty()
    table_columns = ['name','state', 'host','latest_message', 'batch_sys_name', 'submit_method_id', 'submitted_time_string', 'started_time_string', 'finished_time_string', 'mean_elapsed_time']
    for(job in jobs){
        flat_job = reframe_job(jobs[job], table_columns) 
        appendRow(table_name, flat_job, job, table_columns)
    }
}
function reframe_job(job, attributes){
    var reframed_job = [] 
    for(var i = 0; i < attributes.length; i++){
        if(attributes[i] in job && job[attributes[i]] != ""){
            reframed_job.push(job[attributes[i]])
        }
        else{
            reframed_job.push("*")
        }
    }
    return reframed_job
}
function appendRow(table, job, id, columns){
    var tbl = document.getElementById(table), row = tbl.insertRow(tbl.rows.length);
    row.setAttribute('id', id);
    for(var i = 0; i < columns.length; i++){
        var proc_path = id.split(".");
        if(proc_path.length < 2){
            var process_name = "root";
        }
        else{
            var process_name = proc_path[proc_path.length - 1];
        }
        createCell(row.insertCell(i), job[i], columns[i], process_name);
    }
}
function buildName(txt, process_name){
    var state = document.createElement("div")
    var margin = document.createElement("div")
    var div = document.createElement("div")
    state.setAttribute('class', 'circle')
    state.setAttribute('id', 'state_circle')
    margin.setAttribute('id', 'spacing')
    margin.setAttribute('class', 'child-margins')
    div.appendChild(state)
    div.appendChild(margin)
    if(JSON.parse(sessionStorage.getItem('child_counts'))[process_name] > 0){
        var arrow = document.createElement("div")
        arrow.setAttribute('class', 'arrow');
        arrow.setAttribute('id', 'arrow');
        div.appendChild(arrow);
    }
    div.appendChild(txt);
    return div;
}
function createCell(cell, text, column_name, process_name){
    var txt = document.createTextNode(text);
    cell.setAttribute('id', column_name) 
    if(column_name == "name"){
        div = buildName(txt, process_name)
        cell.appendChild(div)
    }
    else{
        cell.appendChild(txt);
    }
}
