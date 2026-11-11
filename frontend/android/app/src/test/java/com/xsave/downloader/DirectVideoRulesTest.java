package com.xsave.downloader;
import org.junit.Test;
import static org.junit.Assert.*;
public class DirectVideoRulesTest {
 @Test public void onlyTrustedHttpsMp4IsAccepted() {
  assertTrue(DirectVideoRules.isMediaUrl("https://video.twimg.com/ext_tw_video/vid/1280x720/test.mp4?tag=12"));
  for(String url:new String[]{"http://video.twimg.com/a.mp4","https://video.twimg.com.evil.test/a.mp4","https://user@video.twimg.com/a.mp4","https://video.twimg.com:8443/a.mp4","https://127.0.0.1/a.mp4","https://video.twimg.com/a.m3u8","https://video.twimg.com/a.mp4#fragment"}) assertFalse(url,DirectVideoRules.isMediaUrl(url));
 }
 @Test public void qualityLabelsUseActualDimensions() {
  assertEquals("1280 × 720 · MP4", DirectVideoRules.qualityLabel("https://video.twimg.com/vid/1280x720/a.mp4",1));
  assertEquals("MP4 option 2", DirectVideoRules.qualityLabel("https://video.twimg.com/a.mp4",2));
 }
}
