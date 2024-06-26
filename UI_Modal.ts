import { App, Modal, Setting } from "obsidian";

export class UI_Modal extends Modal {
    result: string;
    onSubmit: (result: string) => void;

    constructor(app: App, onSubmit: (result: string) => void) {
        super(app);
        this.onSubmit = onSubmit;
    }

    onOpen() {
        const files = this.app.vault.getMarkdownFiles()
        let { contentEl } = this;
        contentEl.createEl("h1", { text: "Enter folder name to search:" });
        new Setting(contentEl)
            .setName("Folder name:")
            .addText((text) =>
                text.onChange((value) => {
                    this.result = value
                }));

        new Setting(contentEl)
            .addButton((btn) =>
                btn
                    .setButtonText("Submit")
                    .setCta()
                    .onClick(() => {
                        this.close();
                        this.onSubmit(this.result);
                    }));
    }

    onClose() {
        let { contentEl } = this;
        contentEl.empty();
    }
}