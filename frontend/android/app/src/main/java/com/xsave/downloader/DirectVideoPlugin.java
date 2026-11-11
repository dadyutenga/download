package com.xsave.downloader;

import android.app.DownloadManager;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.os.Environment;
import com.getcapacitor.*;
import com.getcapacitor.annotation.CapacitorPlugin;
import org.json.*;
import java.net.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

@CapacitorPlugin(name = "DirectVideo")
public class DirectVideoPlugin extends Plugin {
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Map<String, String> formats = new HashMap<>();
    private final Set<Long> downloads = new HashSet<>();
    private DownloadManager manager() { return (DownloadManager)getContext().getSystemService(Context.DOWNLOAD_SERVICE); }

    @PluginMethod public void analyze(PluginCall call) {
        executor.execute(() -> {
            HttpURLConnection connection = null;
            try {
                String id = call.getString("id", ""), token = call.getString("token", "");
                if (!id.matches("[0-9]{1,25}") || !token.matches("[a-z0-9]{1,100}")) throw new IOException("Invalid post link.");
                connection = (HttpURLConnection)new URL("https://cdn.syndication.twimg.com/tweet-result?id=" + id + "&lang=en&token=" + token).openConnection();
                connection.setInstanceFollowRedirects(false);
                connection.setConnectTimeout(20000); connection.setReadTimeout(20000);
                connection.setRequestProperty("User-Agent", "Mozilla/5.0 XSave/2.0");
                if (connection.getResponseCode() != 200) throw new IOException("X could not provide this public post. Try again later.");
                ByteArrayOutputStream body = new ByteArrayOutputStream();
                try (InputStream in = connection.getInputStream()) {
                    byte[] buffer = new byte[8192]; int n;
                    while ((n = in.read(buffer)) != -1) {
                        if (body.size() + n > 2 * 1024 * 1024) throw new IOException("Post response is too large.");
                        body.write(buffer, 0, n);
                    }
                }
                PostVideoParser post = new PostVideoParser(body.toString(StandardCharsets.UTF_8.name()));
                JSArray choices = new JSArray();
                synchronized (formats) {
                    formats.clear();
                    for (PostVideoParser.Format format : post.formats) {
                        String key = UUID.randomUUID().toString(); formats.put(key, format.url);
                        JSObject choice = new JSObject(); choice.put("id", key); choice.put("label", format.label); choices.put(choice);
                    }
                }
                JSObject result = new JSObject(); result.put("title", post.title); result.put("qualities", choices); call.resolve(result);
            } catch (Exception e) { call.reject(e instanceof IOException ? e.getMessage() : "Could not read this post. X may have changed its response."); }
            finally { if (connection != null) connection.disconnect(); }
        });
    }

    @PluginMethod public void download(PluginCall call) {
        try {
            String url; synchronized(formats) { url = formats.get(call.getString("format", "")); }
            if (url == null || !DirectVideoRules.isMediaUrl(url)) { call.reject("Find the video again before downloading."); return; }
            DownloadManager.Request request = new DownloadManager.Request(Uri.parse(url));
            request.setTitle("XSave video"); request.setMimeType("video/mp4");
            request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, "XSave-" + UUID.randomUUID() + ".mp4");
            long id = manager().enqueue(request); synchronized(downloads) { downloads.add(id); }
            JSObject result = new JSObject(); result.put("id", Long.toString(id)); call.resolve(result);
        } catch (Exception e) { call.reject("Could not start Android download. Check storage and your connection."); }
    }
    private long ownedId(PluginCall call) {
        long id = Long.parseLong(call.getString("id", ""));
        synchronized(downloads) { if (!downloads.contains(id)) throw new IllegalArgumentException(); }
        return id;
    }
    @PluginMethod public void status(PluginCall call) {
        try (Cursor c = manager().query(new DownloadManager.Query().setFilterById(ownedId(call)))) {
            if (!c.moveToFirst()) { call.reject("Download was removed from Android Downloads."); return; }
            JSObject result = new JSObject();
            result.put("status", c.getInt(c.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS)));
            result.put("bytes", c.getLong(c.getColumnIndexOrThrow(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR)));
            result.put("total", c.getLong(c.getColumnIndexOrThrow(DownloadManager.COLUMN_TOTAL_SIZE_BYTES)));
            call.resolve(result);
        } catch (Exception e) { call.reject("Could not check download. See Android Downloads for its status."); }
    }
    @PluginMethod public void cancel(PluginCall call) {
        try { manager().remove(ownedId(call)); call.resolve(); }
        catch (Exception e) { call.reject("Could not cancel download."); }
    }
    @Override protected void handleOnDestroy() { executor.shutdownNow(); }
}
