const { ipcRenderer } = require("electron");
const fileList = document.getElementById("fileList");
const processButton = document.getElementById("processButton");
const abortButton = document.getElementById("abortButton");
const previewImage = document.getElementById("previewImage");

let root_data_dir = null;

document.querySelectorAll(".drop-zone").forEach((dropZone, index) => {
  dropZone.addEventListener("click", async () => {
    const folderPath = await ipcRenderer.invoke("open-folder-dialog");

    if (folderPath) {
      console.log(`Drop Zone ${index + 1}: Selected folder ->`, folderPath);

      root_data_dir = folderPath;

      // 添加选中状态的样式类
      dropZone.classList.add("has-selection");
      // 缩短显示的路径
      const shortenedPath = folderPath.split("/").slice(-2).join("/");
      dropZone.textContent = `Selected: .../${shortenedPath}`;

      // Check if all folders are selected, then enable button
      if (root_data_dir) {
        processButton.disabled = false;
      }
    }
  });
});

// 添加IPC监听器来更新预览图
ipcRenderer.on("update-preview", (event, imagePath) => {
  previewImage.src = imagePath;
  previewImage.style.display = "block";
});

// 添加新的IPC监听器来清除预览图
ipcRenderer.on("clear-preview", () => {
  previewImage.style.display = "none";
  previewImage.src = "";
});

processButton.addEventListener("click", async () => {
  if (!root_data_dir) {
    console.log("Please select the root directory before proceeding.");
    return;
  }

  console.log(
    "Processing with folders:",
    root_data_dir
  );

  try {
    processButton.disabled = true;
    processButton.textContent = "Processing...";
    abortButton.disabled = false;

    // 清除之前的预览图
    previewImage.style.display = "none";
    previewImage.src = "";

    const results = await ipcRenderer.invoke(
      "change-skin",
      root_data_dir
    );

    // 如果进程被中止，直接返回，不处理结果
    if (!results) return;

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
    // 只有在非中止情况下才显示错误信息
    if (!error.message?.includes("aborted")) {
      console.error("Error:", error);
      const errorDiv = document.createElement("div");
      errorDiv.textContent = "An error occurred during processing";
      errorDiv.className = "error";
      fileList.appendChild(errorDiv);
    }
  } finally {
    processButton.disabled = false;
    processButton.textContent = "Generate";
    abortButton.disabled = true;
  }
});

// 修改abort按钮的事件监听器，移除重复的预览图清除代码
abortButton.addEventListener("click", async () => {
  try {
    await ipcRenderer.invoke("abort-process");

    // 只显示简单的中止信息
    const messageDiv = document.createElement("div");
    messageDiv.textContent = "Process aborted";
    messageDiv.className = "warning";
    fileList.innerHTML = ""; // 清除之前的所有消息
    fileList.appendChild(messageDiv);

    // 重置按钮状态
    processButton.disabled = false;
    processButton.textContent = "Generate";
    abortButton.disabled = true;
  } catch (error) {
    // 不显示具体错误信息
    console.error("Error aborting process");
  }
});
