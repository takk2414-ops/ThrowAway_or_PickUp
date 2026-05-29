export async function copyTextToClipboard(text: string): Promise<void> {
  if (!navigator.clipboard) {
    throw new Error("このブラウザではクリップボード操作を利用できません。");
  }

  await navigator.clipboard.writeText(text);
}

export function downloadTextFile(filename: string, content: string): void {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  downloadBlobFile(filename, blob);
}

export function downloadBlobFile(filename: string, blob: Blob): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
