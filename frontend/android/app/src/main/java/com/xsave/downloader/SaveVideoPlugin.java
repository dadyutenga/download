package com.xsave.downloader;

import android.app.DownloadManager;
import android.content.Context;
import android.net.Uri;
import android.os.Environment;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.net.URI;

@CapacitorPlugin(name = "SaveVideo")
public class SaveVideoPlugin extends Plugin {
    @PluginMethod
    public void save(PluginCall call) {
        try {
            String value = call.getString("url", "");
            URI uri = new URI(value);
            if (!"https".equals(uri.getScheme()) || uri.getHost() == null || uri.getUserInfo() != null
                || !uri.getPath().matches("/api/v1/downloads/[a-f0-9]{32}/file")
                || uri.getQuery() == null || !uri.getQuery().matches("token=[A-Za-z0-9_-]{40,100}")) {
                call.reject("Invalid download link"); return;
            }
            DownloadManager.Request request = new DownloadManager.Request(Uri.parse(value));
            request.setTitle("XSave video");
            request.setDescription("Saving your video to Downloads");
            request.setMimeType("video/mp4");
            request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, "XSave-" + System.currentTimeMillis() + ".mp4");
            DownloadManager manager = (DownloadManager) getContext().getSystemService(Context.DOWNLOAD_SERVICE);
            long id = manager.enqueue(request);
            JSObject result = new JSObject(); result.put("downloadId", id); call.resolve(result);
        } catch (Exception e) { call.reject("Could not save video. Check Android Downloads and your connection."); }
    }
}
