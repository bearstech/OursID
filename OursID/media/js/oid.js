$(document).ready(function() {

    // sélection du texte de la recherche
    $("#id_email").focus(
        function()
        {
            // only select if the text has not changed
            if(this.value == this.defaultValue)
            {
                this.value='';
            }
        }
    )

});
