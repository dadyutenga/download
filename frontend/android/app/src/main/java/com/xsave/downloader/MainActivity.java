package com.xsave.downloader;
import android.os.Bundle;
import com.getcapacitor.BridgeActivity;
public class MainActivity extends BridgeActivity {
    @Override public void onCreate(Bundle state) {
        registerPlugin(SaveVideoPlugin.class);
        super.onCreate(state);
    }
}
