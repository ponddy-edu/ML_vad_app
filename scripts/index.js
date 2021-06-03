/**
 * Use formatTimeCallback to style the notch labels as you wish, such
 * as with more detail as the number of pixels per second increases.
 *
 * Here we format as M:SS.frac, with M suppressed for times < 1 minute,
 * and frac having 0, 1, or 2 digits as the zoom increases.
 *
 * Note that if you override the default function, you'll almost
 * certainly want to override timeInterval, primaryLabelInterval and/or
 * secondaryLabelInterval so they all work together.
 *
 * @param: seconds
 * @param: pxPerSec
 */
function formatTimeCallback(seconds, pxPerSec) {
    seconds = Number(seconds);
    var minutes = Math.floor(seconds / 60);
    seconds = seconds % 60;

    // fill up seconds with zeroes
    var secondsStr = Math.round(seconds).toString();
    if (pxPerSec >= 25 * 10) {
        secondsStr = seconds.toFixed(2);
    } else if (pxPerSec >= 25 * 1) {
        secondsStr = seconds.toFixed(1);
    }

    if (minutes > 0) {
        if (seconds < 10) {
            secondsStr = '0' + secondsStr;
        }
        return `${minutes}:${secondsStr}`;
    }
    return secondsStr;
}

/**
 * Use timeInterval to set the period between notches, in seconds,
 * adding notches as the number of pixels per second increases.
 *
 * Note that if you override the default function, you'll almost
 * certainly want to override formatTimeCallback, primaryLabelInterval
 * and/or secondaryLabelInterval so they all work together.
 *
 * @param: pxPerSec
 */
function timeInterval(pxPerSec) {
    var retval = 1;
    /*
    if (pxPerSec >= 25 * 100) {
        retval = 0.01;
    } else if (pxPerSec >= 25 * 40) {
        retval = 0.025;
    } else if (pxPerSec >= 25 * 10) {
        retval = 0.1;
    } else if (pxPerSec >= 25 * 4) {
        retval = 0.25;
    } else if (pxPerSec >= 25) {
        retval = 1;
    } else if (pxPerSec * 5 >= 25) {
        retval = 5;
    } else if (pxPerSec * 15 >= 25) {
        retval = 15;
    } else {
        retval = Math.ceil(0.5 / pxPerSec) * 60;
    }*/
    if (pxPerSec >= 600) {
        retval = 0.01;
    }
    else if (pxPerSec >= 500) {
        retval = 0.02;
    }
    else if (pxPerSec >= 400) {
        retval = 0.05;
    }
    else if (pxPerSec >= 300) {
        retval = 0.1;
    }
    return retval;
}

/**
 * Return the cadence of notches that get labels in the primary color.
 * EG, return 2 if every 2nd notch should be labeled,
 * return 10 if every 10th notch should be labeled, etc.
 *
 * Note that if you override the default function, you'll almost
 * certainly want to override formatTimeCallback, primaryLabelInterval
 * and/or secondaryLabelInterval so they all work together.
 *
 * @param pxPerSec
 */
function primaryLabelInterval(pxPerSec) {
    var retval = 1;
    /*
    if (pxPerSec >= 25 * 100) {
        retval = 100;
    } else if (pxPerSec >= 25 * 40) {
        retval = 40;
    } else if (pxPerSec >= 25 * 10) {
        retval = 100;
    } else if (pxPerSec >= 25 * 4) {
        retval = 40;
    } else if (pxPerSec >= 25) {
        retval = 1;
    } else if (pxPerSec * 5 >= 25) {
        retval = 5;
    } else if (pxPerSec * 15 >= 25) {
        retval = 15;
    } else {
        retval = Math.ceil(0.5 / pxPerSec) * 60;
    } */
    if (pxPerSec >= 600) {
        retval = 5;
    }
    else if (pxPerSec >= 500) {
        retval = 7;
    }
    else if (pxPerSec >= 400) {
        retval = 8;
    }
    else if (pxPerSec >= 300) {
        retval = 10;
    }
    return retval;
}

/**
 * Return the cadence of notches to get labels in the secondary color.
 * EG, return 2 if every 2nd notch should be labeled,
 * return 10 if every 10th notch should be labeled, etc.
 *
 * Secondary labels are drawn after primary labels, so if
 * you want to have labels every 10 seconds and another color labels
 * every 60 seconds, the 60 second labels should be the secondaries.
 *
 * Note that if you override the default function, you'll almost
 * certainly want to override formatTimeCallback, primaryLabelInterval
 * and/or secondaryLabelInterval so they all work together.
 *
 * @param pxPerSec
 */
function secondaryLabelInterval(pxPerSec) {
    // draw one every 10s as an example
    return Math.floor(2 / timeInterval(pxPerSec));
}

function randomColor(alpha) {
    return (
        'rgba(' +
        [
            ~~(Math.random() * 255),
            ~~(Math.random() * 255),
            ~~(Math.random() * 255),
            alpha || 1
        ] +
        ')'
    );
}

$(document).ready(function(){

    $("#btn-upload").click(function(){
        var form = $('#upload-form')[0];
        var formData = new FormData(form);
        $("#btn-upload").css("display", "none");
        $(".spinner-border").fadeIn();
        $.ajax({
            // xhr: function(){
            //     var xhr = new window.XMLHttpRequest();
            //     xhr.upload.addEventListener("progress", function(evt){
            //         if(evt.lengthComputable){
            //             var percentComplete = evt.loaded / evt.total;
            //             percentComplete = parseInt(percentComplete * 100);
            //             var percentVal = percentComplete + "%";
            //             $(".progress-bar").css("width", percentVal);
            //             $(".progress-bar").attr("aria-valuenow", percentComplete);
            //             $(".progress-bar").html(percentVal + " Complete");
            //             // console.log(percentComplete);
            //         }
            //     }, false);
            //     return xhr;
            // },
            url: '/',
            data: formData,
            type: "POST",
            contentType: false,
            processData: false,
            success: function(data){
                // console.log(data);      
                if(data["error"] == false){
                    var main_video = $('<video />', {
                        id: "main-video",
                        src: data["origin_video"],
                        controls: true,
                        width: 960,
                        height: 540
                    });
                    main_video.appendTo($("#main-video-block"));

                    for(var i=0; i<data["data"].length; i++){
                        var tmp_div = $('<div />', {
                            class: "subclip-div",
                            id: "subclip-div-" + i.toString()
                        });

                        var tmp_video = $('<video />', {
                            src: data["data"][i]["filename"],
                            controls: true,
                            width: 320,
                            height: 180
                        });

                        var tmp_video_div = $('<div />', {
                            class: "subclip",
                            id: "subclip-" + i.toString(),
                        });

                        var main_waveform = document.createElement('div');
                        main_waveform.setAttribute("id", "waveform-" + i.toString());
                        main_waveform.setAttribute("class", "waveforms");
                        var waveform_timeline = document.createElement('div');
                        waveform_timeline.setAttribute("id", "waveform-timeline-" + i.toString());
                       
                        var wavesurfer = WaveSurfer.create({
                            container: main_waveform,
                            waveColor: '#A8DBA8',
                            progressColor: '#3B8686',
                            backend: 'MediaElement',
                            plugins: [
                                WaveSurfer.regions.create({
                                    // regions: [
                                    //     {
                                    //         start: 0.5,
                                    //         end: 1,
                                    //         color: 'hsla(400, 100%, 30%, 0.5)'
                                    //     }, {
                                    //         start: 1,
                                    //         end: 2,
                                    //         color: 'hsla(200, 50%, 70%, 0.4)'
                                    //     }
                                    // ],
                                    // dragSelection: {
                                    //     slop: 5
                                    // }
                                }),
                                WaveSurfer.timeline.create({
                                    wavesurfer: wavesurfer,
                                    container: waveform_timeline,
                                    formatTimeCallback: formatTimeCallback,
                                    timeInterval: timeInterval,
                                    primaryLabelInterval: primaryLabelInterval,
                                    secondaryLabelInterval: secondaryLabelInterval,
                                    primaryColor: 'blue',
                                    secondaryColor: 'red',
                                    primaryFontColor: 'blue',
                                    secondaryFontColor: 'red',
                                    labelPadding: 1 
                                })//,
                                // WaveSurfer.cursor.create({
                                //     showTime: true,
                                //     opacity: 1,
                                //     customShowTimeStyle: {
                                //         'background-color': '#000',
                                //         color: '#fff',
                                //         padding: '2px',
                                //         'font-size': '10px'
                                //     }
                                // })    
                            ]
                        });

                        for(var j=0; j<data["data"][i]["ctm"].length; j++){
                            var cur = data["data"][i]["ctm"][j];
                            var wordData = [cur["word"], cur["score"]];
                            var begin = cur["begin"];
                            var end = cur["end"];
                            wavesurfer.addRegion({
                                id: j,
                                start: begin,
                                end: end,
                                data: wordData,
                                color: randomColor(0.2)
                            });
                        }

                        wavesurfer.zoom(400);
    
                        wavesurfer.load(data["data"][i]["wavclip_filepath"]);
                        wavesurfer.on('region-click', function(region, e) {
                            //console.log(region.start);
                            //console.log(region.end);
                            e.stopPropagation();
                            region.play();
                        });
                        

                        var tmp_text = $('<div />', {
                            class: "subclip-text",
                            id: "subclip-text-" + i.toString()
                        }).html(data["data"][i]["text"]);

                        var tmp_subblock = $('<div />', {
                            class: "subclip-rightsubblock",
                            id: "subclip-rightsubblock-" + i.toString()
                        });

                        tmp_video.appendTo(tmp_video_div);
                        tmp_video_div.appendTo(tmp_div);
                        // tmp_text.appendTo(tmp_div);
                        tmp_div.appendTo($("#subclip-block"));
                        tmp_subblock.append(main_waveform).append(tmp_text);
                        tmp_div.append(tmp_subblock);

                    }
                    $("#upload-form").fadeOut();
                    $("#btn-goback").fadeIn();

                    

                    // $(".btn-primary").click(function(){
                    //     wavesurfer.playPause()
                    // });
                }
                else{
                    $('#upload-form')[0].reset();
                    // $(".progress-bar").css("width", "0%");
                    // $(".progress-bar").attr("aria-valuenow", 0);
                    // $(".progress-bar").html("0% complete");
                    alert(data["err_msg"]);
                    window.location.reload();
                }
            }
        });
    });

    $("#btn-goback").click(function(){        
        $("#upload-form").fadeIn();
        $("#btn-goback").css("display", "none");
        $('#upload-form')[0].reset();
        $("#file").css("display", "none");
        $("#subclip-block").empty();
        $("#main-video-block").empty();
        $("#youtube-url-input").attr("value", "").css("display", "inline");
        $("#btn-upload").css("display", "inline");
        $(".spinner-border").css("display", "none");
        $("#voice_threshold_text").text('0.4');
        $("#sil_duration_threshold_text").text('0.1');
        $("#voice_duration_threshold_text").text('0.3');
    });
});
