const { ipcRenderer } = require("electron");
const fileList = document.getElementById("fileList");
const processButton = document.getElementById("processButton");
const abortButton = document.getElementById("abortButton");

let selectedFiles = [];

let input_data_dir = null;
let resources_dir = null;
let output_data_dir = null;

document.querySelectorAll(".drop-zone").forEach((dropZone, index) => {
  dropZone.addEventListener("click", async () => {
    const folderPath = await ipcRenderer.invoke("open-folder-dialog");

    if (folderPath) {
      console.log(`Drop Zone ${index + 1}: Selected folder ->`, folderPath);

      // Store in different variables
      if (index === 0) input_data_dir = folderPath;
      if (index === 1) resources_dir = folderPath;
      if (index === 2) output_data_dir = folderPath;

      dropZone.textContent = `Selected: ${folderPath}`;

      // Check if all folders are selected, then enable button
      if (input_data_dir && resources_dir && output_data_dir) {
        processButton.disabled = false;
      }
    }
  });
});

processButton.addEventListener("click", async () => {
  if (!input_data_dir || !resources_dir || !output_data_dir) {
    console.log("Please select all three folders before proceeding.");
    return;
  }

  console.log(
    "Processing with folders:",
    input_data_dir,
    resources_dir,
    output_data_dir
  );

  try {
    processButton.disabled = true;
    processButton.textContent = "Processing...";
    abortButton.disabled = false;

    const results = await ipcRenderer.invoke(
      "change-skin",
      input_data_dir,
      resources_dir,
      output_data_dir
    );
    console.log("check: ", results);

    const jsonObj = JSON.parse(results);

    fileList.innerHTML = "";
    jsonObj.forEach((result) => {
      const item = document.createElement("div");
      if (result.success) {
        item.textContent = `Successfully processed. Output saved in: ${result.output_path}`;
        item.className = "success";
      } else {
        item.textContent = `Error: ${result.error}`;
        item.className = "error";
      }
      fileList.appendChild(item);
    });
  } catch (error) {
    console.error("renderer.js: Error:", error);
    const errorDiv = document.createElement("div");
    errorDiv.textContent = `Error generating: ${error}`;
    errorDiv.className = "error";
    fileList.appendChild(errorDiv);
  } finally {
    processButton.disabled = false;
    processButton.textContent = "Generate";
    abortButton.disabled = true;
  }
});

abortButton.addEventListener("click", async () => {
  try {
    await ipcRenderer.invoke("abort-process");
    const errorDiv = document.createElement("div");
    errorDiv.textContent = "Process aborted by user";
    errorDiv.className = "warning";
    fileList.appendChild(errorDiv);
  } catch (error) {
    console.error("Error aborting process:", error);
  }
});
