$(document).ready(function() {
    $('head', document).append('<link rel="stylesheet" type="text/css" media="screen" href="/media/cms/wymeditor/skins/default/skin.css" />');
    $("textarea").wymeditor({
        updateSelector: "input:submit",
        updateEvent:    "click"    
    });
});
