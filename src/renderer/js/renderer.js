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
  //previewImage.src = imagePath;
  previewImage.src = `${imagePath}?t=${Date.now()}`;
  previewImage.style.display = "block";
});

processButton.addEventListener("click", async () => {
  if (!root_data_dir) {
    console.log("Please select the root directory before proceeding.");
    return;
  }

  console.log("Processing with folders:", root_data_dir);

  try {
    processButton.disabled = true;
    processButton.textContent = "Processing...";
    abortButton.disabled = false;

    const results = await ipcRenderer.invoke("change-skin", root_data_dir);

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
    // 添加更详细的错误日志
    console.log("Detailed error information:", {
      message: error.message,
      stack: error.stack,
      fullError: error,
      type: error.constructor.name,
    });

    // 检查是否是abort相关的错误
    const isAbortError =
      error.message?.includes("aborted") ||
      error.message?.includes("change-skin");

    if (!isAbortError) {
      console.error("Non-abort error details:", error.message);
      const errorDiv = document.createElement("div");
      errorDiv.textContent = "An error occurred during processing";
      errorDiv.className = "error";
      fileList.appendChild(errorDiv);
    } else {
      console.log("Abort error caught, skipping error message");
    }
  } finally {
    processButton.disabled = false;
    processButton.textContent = "Generate";
    abortButton.disabled = true;
  }
});

// 修改abort按钮的事件监听器
abortButton.addEventListener("click", async () => {
  console.log("Abort button clicked");
  try {
    await ipcRenderer.invoke("abort-process");
    console.log("Abort process completed");

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
    // 添加详细的错误日志
    console.log("Error in abort button handler:", {
      errorMessage: error.message,
      errorStack: error.stack,
    });
    console.error("Error aborting process");
  }
});

// 移除clear-preview的监听器，因为我们不再需要它
ipcRenderer.removeAllListeners("clear-preview");
