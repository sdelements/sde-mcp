export function checkNodeVersion(): void {
  const version = process.version;
  const majorVersion = parseInt(version.slice(1).split(".")[0], 10);
  const MINIMUM_VERSION = 22;

  if (majorVersion < MINIMUM_VERSION) {
    console.error(
      `WARNING: Node.js version ${version} is not supported. ` +
        `This MCP server requires Node.js v${MINIMUM_VERSION} or higher. ` +
        `Please upgrade your Node.js installation.`
    );
    console.error(`Current version: ${version}`);
    console.error(`Minimum required: v${MINIMUM_VERSION}.0.0`);
    process.exit(1);
  }

  console.info(`Node.js version ${version} detected (OK)`);
}
