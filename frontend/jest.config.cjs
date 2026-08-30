module.exports = {
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  testMatch: ["**/tests/**/*.spec.ts?(x)", "**/tests/**/*.test.ts?(x)"]
};
