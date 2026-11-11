import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import NativeApp from './NativeApp';
import {Capacitor} from '@capacitor/core';
const Root=Capacitor.isNativePlatform()?NativeApp:App;
import './styles/app.css';
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><Root/></React.StrictMode>);
