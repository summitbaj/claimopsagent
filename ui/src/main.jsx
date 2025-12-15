import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { PublicClientApplication } from "@azure/msal-browser";
import { MsalProvider } from "@azure/msal-react";
import { msalConfig } from "./authConfig";

const msalInstance = new PublicClientApplication(msalConfig);

// Initialize MSAL v3+ before rendering
// Initialize MSAL v3+ and handle redirect
msalInstance.initialize().then(() => {
    // Handle redirect promise for handling auth responses
    msalInstance.handleRedirectPromise().then(() => {
        ReactDOM.createRoot(document.getElementById('root')).render(
            <React.StrictMode>
                <MsalProvider instance={msalInstance}>
                    <App />
                </MsalProvider>
            </React.StrictMode>,
        );
    }).catch(e => {
        console.error(e);
    });
});
