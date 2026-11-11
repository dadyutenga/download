package com.xsave.downloader;
import org.json.*;
import java.io.IOException;
import java.util.*;

final class PostVideoParser {
    static final class Format {
        final String url, label;
        Format(String url, String label) { this.url=url; this.label=label; }
    }
    final String title;
    final List<Format> formats = new ArrayList<>();
    PostVideoParser(String json) throws JSONException, IOException {
        JSONObject post = new JSONObject(json);
        title = post.optString("text", "X video");
        JSONArray variants = post.optJSONObject("video") == null ? null : post.getJSONObject("video").optJSONArray("variants");
        JSONArray details = post.optJSONArray("mediaDetails");
        if (details != null) {
            for (int i=0;i<details.length();i++) {
                JSONObject detail=details.optJSONObject(i);
                JSONObject info=detail==null?null:detail.optJSONObject("video_info");
                if (info!=null && info.optJSONArray("variants")!=null) { variants=info.optJSONArray("variants"); break; }
            }
        }
        if (variants != null) {
            Set<String> seen = new HashSet<>();
            for (int i=0;i<variants.length();i++) {
                JSONObject variant=variants.optJSONObject(i);
                if (variant==null) continue;
                String url=variant.optString("url", variant.optString("src"));
                if ("video/mp4".equals(variant.optString("content_type", variant.optString("type"))) && DirectVideoRules.isMediaUrl(url) && seen.add(url))
                    formats.add(new Format(url, DirectVideoRules.qualityLabel(url, formats.size()+1)));
            }
        }
        if (formats.isEmpty()) throw new IOException("No supported public MP4 video found. Private posts, live streams, and unavailable embeds are not supported.");
    }
}
