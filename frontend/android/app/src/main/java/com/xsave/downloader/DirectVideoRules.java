package com.xsave.downloader;
import java.net.URI;
import java.util.regex.*;

final class DirectVideoRules {
    static boolean isMediaUrl(String value) {
        try {
            URI uri = new URI(value);
            return "https".equals(uri.getScheme()) && "video.twimg.com".equals(uri.getHost())
                && uri.getUserInfo() == null && (uri.getPort() == -1 || uri.getPort() == 443)
                && uri.getFragment() == null && uri.getPath().endsWith(".mp4");
        } catch (Exception e) { return false; }
    }
    static String qualityLabel(String url, int index) {
        Matcher m = Pattern.compile("/(\\d+)x(\\d+)/").matcher(url);
        return m.find() ? m.group(1) + " × " + m.group(2) + " · MP4" : "MP4 option " + index;
    }
}
