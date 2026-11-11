package com.xsave.downloader;
import org.junit.Test;
import static org.junit.Assert.*;
import java.io.IOException;
public class PostVideoParserTest {
 @Test public void extractsPublicEmbedMp4VariantsAndRejectsOtherHosts() throws Exception {
  PostVideoParser post=new PostVideoParser("{\"text\":\"Fixture video\",\"video\":{\"variants\":[{\"type\":\"application/x-mpegURL\",\"src\":\"https://video.twimg.com/a.m3u8\"},{\"type\":\"video/mp4\",\"src\":\"https://video.twimg.com/vid/1280x720/a.mp4\"},{\"type\":\"video/mp4\",\"src\":\"https://evil.test/a.mp4\"},{\"type\":\"video/mp4\",\"src\":\"https://video.twimg.com/vid/1280x720/a.mp4\"}]}}");
  assertEquals("Fixture video",post.title);assertEquals(1,post.formats.size());assertEquals("1280 × 720 · MP4",post.formats.get(0).label);
 }
 @Test public void extractsMediaDetailsResponse() throws Exception {
  PostVideoParser post=new PostVideoParser("{\"mediaDetails\":[{\"type\":\"photo\"},{\"video_info\":{\"variants\":[{\"content_type\":\"video/mp4\",\"url\":\"https://video.twimg.com/vid/640x360/a.mp4\"}]}}]}");
  assertEquals(1,post.formats.size());assertEquals("640 × 360 · MP4",post.formats.get(0).label);
 }
 @Test(expected=IOException.class) public void unavailablePostIsAnError() throws Exception { new PostVideoParser("{}"); }
 @Test(expected=IOException.class) public void noProgressiveMp4IsAnError() throws Exception { new PostVideoParser("{\"video\":{\"variants\":[]}}"); }
}
