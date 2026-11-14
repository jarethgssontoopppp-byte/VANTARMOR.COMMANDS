(() => {
  const MAX_FILE_BYTES = 5 * 1024 * 1024;
  const MAX_DATA_BYTES = 2 * 1024 * 1024;

  function setStatus(message) {
    const status = document.querySelector("#guild-profile-message");
    if (status) status.textContent = message;
  }

  async function imageAsDataUri(file) {
    if (!file || !file.type.startsWith("image/")) throw new Error("Selecciona un archivo de imagen.");
    if (file.size > MAX_FILE_BYTES) throw new Error("La imagen original debe pesar menos de 5 MB.");
    let bitmap;
    try {
      bitmap = await createImageBitmap(file);
      const scale = Math.min(1, 512 / Math.max(bitmap.width, bitmap.height));
      const canvas = document.createElement("canvas");
      canvas.width = Math.max(1, Math.round(bitmap.width * scale));
      canvas.height = Math.max(1, Math.round(bitmap.height * scale));
      canvas.getContext("2d").drawImage(bitmap, 0, 0, canvas.width, canvas.height);
      const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/webp", 0.86));
      if (!blob) throw new Error("No se pudo procesar la imagen.");
      if (blob.size > MAX_DATA_BYTES) throw new Error("La imagen procesada supera 2 MB.");
      const dataUri = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(new Error("No se pudo leer la imagen."));
        reader.readAsDataURL(blob);
      });
      return dataUri;
    } finally {
      bitmap?.close();
    }
  }

  function attachUpload(form) {
    if (!form || form.dataset.profileUploadReady === "true") return;
    const urlInput = form.querySelector("#profile-avatar-url");
    if (!urlInput) return;
    form.dataset.profileUploadReady = "true";
    const wrapper = document.createElement("label");
    wrapper.className = "profile-upload-field";
    wrapper.style.cssText = "display:grid;gap:.45rem;margin:.75rem 0";
    wrapper.textContent = "O sube una imagen para el avatar del bot en este servidor (máximo 5 MB):";
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "image/png,image/jpeg,image/webp,image/gif";
    input.setAttribute("aria-label", "Subir imagen para el avatar del bot");
    wrapper.append(input);
    urlInput.insertAdjacentElement("afterend", wrapper);

    input.addEventListener("change", async () => {
      const file = input.files?.[0];
      if (!file) return;
      try {
        setStatus("Procesando imagen…");
        urlInput.type = "text";
        urlInput.value = await imageAsDataUri(file);
        urlInput.dataset.uploadedImage = "true";
        setStatus("Imagen lista. Pulsa Guardar ajustes para aplicarla.");
      } catch (error) {
        input.value = "";
        urlInput.value = "";
        setStatus(error.message || "No se pudo procesar la imagen.");
      }
    });

    urlInput.addEventListener("input", () => {
      if (urlInput.dataset.uploadedImage === "true") {
        delete urlInput.dataset.uploadedImage;
        urlInput.type = "url";
        input.value = "";
      }
    });
  }

  const observer = new MutationObserver(() => {
    const form = document.querySelector("#guild-profile-form");
    if (form) attachUpload(form);
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });
  attachUpload(document.querySelector("#guild-profile-form"));
})();
