import { safeDownloadFilename, validateUpload } from "../../src/lib/security/file-security";

describe("file security", () => {
  it("allows constrained PDF uploads", () => {
    expect(validateUpload({ name: "evidence.pdf", type: "application/pdf", size: 1024 })).toEqual([]);
  });
  it("rejects dangerous executable extensions", () => {
    expect(validateUpload({ name: "invoice.pdf.exe", type: "application/pdf", size: 1024 })).toContain("dangerous_extension");
  });
  it("normalizes download filenames", () => {
    expect(safeDownloadFilename("..\\report\r\n.pdf")).not.toMatch(/[\\\r\n]/);
  });
});
