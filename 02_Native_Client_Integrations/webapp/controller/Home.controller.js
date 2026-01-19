sap.ui.define([
    "sap/ui/core/mvc/Controller",
    "sap/m/MessageToast",
    "sap/ui/model/json/JSONModel"
], function (Controller, MessageToast, JSONModel) {
    "use strict";

    return Controller.extend("native.integrations.controller.Home", {
        onInit: function () {
            var oModel = new JSONModel({
                responseResult: ""
            });
            this.getView().setModel(oModel);
        },

        onRunValues: function () {
            var oView = this.getView();
            var sProvider = oView.byId("providerSelect").getSelectedKey();
            var sPrompt = oView.byId("promptInput").getValue();

            if (!sPrompt) {
                MessageToast.show("Please enter a prompt.");
                return;
            }

            var oModel = oView.getModel();
            oView.byId("busyIndicator").setVisible(true);
            oModel.setProperty("/responseResult", ""); // Clear previous result

            // Call Backend API
            fetch("http://localhost:8090/api/analyze", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    provider: sProvider,
                    prompt: sPrompt
                })
            })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(err => { throw new Error(err.detail || "Server Error"); });
                    }
                    return response.json();
                })
                .then(data => {
                    oModel.setProperty("/responseResult", data.result);
                })
                .catch(error => {
                    MessageToast.show("Error: " + error.message);
                    oModel.setProperty("/responseResult", "Error: " + error.message);
                })
                .finally(() => {
                    oView.byId("busyIndicator").setVisible(false);
                });
        }
    });
});
