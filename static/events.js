
// function getCookie(name) {
//     var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
//     return r ? r[1] : undefined;
// }

// jQuery.postJSON = function(url, args, callback) {
//     args._xsrf = getCookie("_xsrf");
//     $.ajax({url: url, data: $.param(args), dataType: "text", type: "POST",
//         success: function(response) {
//         callback(eval("(" + response + ")"));
//     }});
// };
function uuidv4() {
    return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
      (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
}

window.onload=function(){
    const myForm = document.getElementById("myForm");
    const inpFile = document.getElementById("myfiles");
    if (myForm){
    myForm.addEventListener("submit", async e => {
        e.preventDefault();
        const host = "http://localhost:8000/upload/";
        const formData = new FormData(); 
        for (var i=0; i<inpFile.files.length; i++) {
            const file = inpFile.files[i];
            const file_size = file.size;
            const fileName = uuidv4() + inpFile.files[0].name
            let metadata = {
                filename: fileName
            };
            formData.append("myfiles", inpFile.files[0]);
            const chunkSize = 256 * 1024;
            let post_reponse = await fetch(host, {
            method: 'post',
            body: JSON.stringify(metadata)
            });
            console.log(post_reponse)
            if (post_reponse.status == '200'){
                const endpoint = host + encodeURIComponent(fileName);
                var start = 0;
                var chunkEnd = start + chunkSize
                var chunk = file.slice(start, chunkEnd)
                while (true){
                    let put_response = fetch(endpoint, {
                        method: 'put',
                        body: chunk,
                        headers: {
                            'Content-Range': start + "-" + chunkEnd + "/" + file.size,
                            'File-Size': file_size,
                        }
                    });
                    console.log(file.size);
                    console.log("Status " + (await put_response).status);
                    var bytes_read = parseInt((await put_response).headers.get('Range'));
                    document.getElementById("process").innerHTML = (chunkEnd) / file_size;
                    console.log('Bytes read ' + bytes_read)
                    if ((await put_response).status == '200'){
                        document.getElementById("process").innerHTML = ((chunkEnd) / file_size)*100;
                        //location.reload();
                        document.getElementById("process").innerHTML = "Done";
                        break;
                    }else if((await put_response).status == '308'){
                        document.getElementById("process").innerHTML = ((chunkEnd) / file_size)*100;
                        start += bytes_read;
                        chunkEnd = Math.min(start + chunkSize, file.size);
                        chunk = file.slice(start, chunkEnd);
                        console.log("Start byte " + start);
                        console.log("End byte " + chunkEnd);
                    }
                    // else {
                    //     start = 0;
                    //     chunkEnd = chunkSize;
                    // }
                }
            }
    }
});
}
}



