import api from "../api/client";

/**
 * Finds all images in the container that are protected (e.g. start with /notes/files/ or /notes/share-files/)
 * and fetches them with authentication headers, replacing the src with a blob URL.
 */
export const replaceImagesWithSecureUrls = async (container: HTMLElement) => {
  if (!container) return;

  const images = container.querySelectorAll("img");
  
  images.forEach(async (img) => {
    const src = img.dataset.secureOriginal || img.getAttribute("src");
    
    // Process paths containing /notes/files/
    // This handles both /notes/files/... and /api/notes/files/...
    if (src && (src.includes("/notes/files/") || src.includes("/notes/share-files/")) && !src.startsWith("blob:")) {
      try {
        // Check if we already have a loading flag to avoid double fetch
        if (img.dataset.loaded === "true" || img.dataset.loaded === "error") return;
        if (img.dataset.loading === "true") return;
        img.dataset.loading = "true";
        if (!img.dataset.secureOriginal) {
          img.dataset.secureOriginal = src;
        }
        if (!img.dataset.secureHidden) {
          img.dataset.secureHidden = "true";
          img.style.visibility = "hidden";
          img.style.opacity = "0";
          img.style.transition = "opacity 150ms ease";
        }

        // Handle URL adjustment for api client
        let requestPath = src;
        // Try to extract the path starting from /notes/files/
        const match = src.match(/(\/notes\/(?:share-files|files)\/.*)/);
        if (match) {
          requestPath = match[1];
        }
        
        // Fetch with auth headers
        const response = await api.get(requestPath, { responseType: "blob" });
        const blobUrl = URL.createObjectURL(response.data);
        
        const handleLoad = () => {
          img.style.visibility = "visible";
          img.style.opacity = "1";
          img.removeEventListener("load", handleLoad);
        };
        img.addEventListener("load", handleLoad);
        img.src = blobUrl;
        img.removeAttribute("srcset");
        img.dataset.loaded = "true";
      } catch (error) {
        console.error("Failed to load secure image:", src, error);
        img.dataset.loaded = "error";
      } finally {
        img.dataset.loading = "false";
      }
    }
  });
};
