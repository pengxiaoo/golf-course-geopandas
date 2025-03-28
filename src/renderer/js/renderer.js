const { ipcRenderer } = require('electron')
const dropZone = document.getElementById('dropZone')
const fileList = document.getElementById('fileList')
const processButton = document.getElementById('processButton')

let selectedFiles = []

// Disable by security html5 and javascript
// dropZone.addEventListener('dragover', (e) => {
//     e.preventDefault()
//     e.stopPropagation()
//     dropZone.classList.add('drag-over')
// })

// dropZone.addEventListener('dragleave', (e) => {
//     e.preventDefault()
//     e.stopPropagation()
//     dropZone.classList.remove('drag-over')
// })

// dropZone.addEventListener('drop', (e) => {
//     e.preventDefault()
//     e.stopPropagation()
//     dropZone.classList.remove('drag-over')
    
//     const files = Array.from(e.dataTransfer.files)
//     handleFiles(files)
// })

dropZone.addEventListener('click', async () => {
    const filePaths = await ipcRenderer.invoke('open-file-dialog');

    if (filePaths && filePaths.length > 0) {
        const files = Array.from(filePaths)
        console.log('renderer.js: Files array:', files)
        
        handleFiles(files)
    }
})

function handleFiles(files) {
    selectedFiles = files.map(file => {
        console.log('renderer.js: Processing file:', file)
        const path = file.path || file.webkitRelativePath || file.name
        console.log('renderer.js: Got path:', path)
        return file
    })
    
  
    console.log('renderer.js: Final selected file paths:', selectedFiles)
    // todo: the log shows selectedFiles only has the file name, not the full path. log copied below:
    // "renderer.js: Final selected file paths: ['cb_report_for_the_past_7_days_2025-03-08T21_04_41.127598-05_00.xlsx', 'main_cb_report_2025-03-08T20_47_00.340088-05_00.csv']"
    fileList.innerHTML = ''
    files.forEach(file => {
        const item = document.createElement('div')
        const fileName = file.split('/').pop();
        item.textContent = `${fileName} (${file || 'path not available'})`
        fileList.appendChild(item)
    })
    processButton.disabled = selectedFiles.length === 0
}

processButton.addEventListener('click', async () => {
    if (selectedFiles.length === 0) return    

    try {
        processButton.disabled = true
        processButton.textContent = 'Processing...'
        
        const results = await ipcRenderer.invoke('process-files', selectedFiles)
        console.log("check: ", results);
        
        const jsonObj = JSON.parse(results);
        
        fileList.innerHTML = ''
        jsonObj.forEach(result => {
            const item = document.createElement('div')
            if (result.success) {
                item.textContent = `Successfully processed. Output saved in: ${result.output_path}`
                item.className = 'success'
            } else {
                item.textContent = `Error: ${result.error}`
                item.className = 'error'
            }
            fileList.appendChild(item)
        })
    } catch (error) {
        console.error('renderer.js: Error:', error)
        const errorDiv = document.createElement('div')
        errorDiv.textContent = `Error processing files: ${error}`
        errorDiv.className = 'error'
        fileList.appendChild(errorDiv)
    } finally {
        processButton.disabled = false
        processButton.textContent = 'Process Files'
    }
}) 