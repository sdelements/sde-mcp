/**
 * Mapping utilities: detect survey answers from project context
 * Ported from the original Python server extract_answer_texts_from_context.
 */

/**
 * Extract relevant answer texts from a freeform context string by matching
 * against available survey answers.
 */
export function extractAnswerTextsFromContext(
  codeContext: string,
  availableAnswers: Array<{ text?: string }>
): string[] {
  if (!codeContext) return [];
  const codeContextLower = codeContext.toLowerCase();
  const matched: string[] = [];

  // Common technology mappings (order matters; longer first)
  const technologyKeywords: Array<[string, string]> = [
    // Application types
    ["rest api", "REST API"],
    ["restful api", "REST API"],
    ["restful", "REST API"],
    ["web application", "Web Application"],
    ["web app", "Web Application"],
    ["webapp", "Web Application"],
    ["mobile application", "Mobile Application"],
    ["mobile app", "Mobile Application"],
    ["desktop application", "Desktop Application"],
    ["desktop app", "Desktop Application"],
    ["microservices", "Microservices"],
    ["microservice", "Microservices"],

    // Cloud platforms
    ["amazon web services", "AWS"],
    ["google cloud platform", "Google Cloud Platform"],
    ["google cloud", "Google Cloud Platform"],
    ["microsoft azure", "Azure"],

    // Programming languages
    ["javascript", "JavaScript"],
    ["typescript", "TypeScript"],
    ["node.js", "Node.js"],
    ["nodejs", "Node.js"],
    ["golang", "Go"],
    ["csharp", "C#"],
    ["ruby on rails", "Ruby on Rails"],
    ["spring boot", "Spring Boot"],
    ["python", "Python"],
    ["java", "Java"],
    ["go", "Go"],
    ["rust", "Rust"],
    ["php", "PHP"],
    ["ruby", "Ruby"],
    ["swift", "Swift"],
    ["kotlin", "Kotlin"],
    ["scala", "Scala"],
    ["r language", "R"],
    ["r programming", "R"],
    ["matlab", "MATLAB"],

    // Databases
    ["postgresql", "PostgreSQL"],
    ["postgres", "PostgreSQL"],
    ["sql server", "SQL Server"],
    ["oracle database", "Oracle Database"],
    ["mysql", "MySQL"],
    ["mongodb", "MongoDB"],
    ["redis", "Redis"],
    ["cassandra", "Cassandra"],
    ["sqlite", "SQLite"],
    ["dynamodb", "DynamoDB"],
    ["elasticsearch", "Elasticsearch"],

    // Frameworks / tools
    ["vue.js", "Vue.js"],
    ["spring", "Spring"],
    ["react", "React"],
    ["angular", "Angular"],
    ["vue", "Vue.js"],
    ["express", "Express"],
    ["django", "Django"],
    ["flask", "Flask"],
    ["rails", "Ruby on Rails"],
    ["laravel", "Laravel"],
    ["kubernetes", "Kubernetes"],
    ["k8s", "Kubernetes"],
    ["docker", "Docker"],

    // Security / auth
    ["oauth 2.0", "OAuth 2.0"],
    ["oauth2", "OAuth 2.0"],
    ["oauth", "OAuth"],
    ["jwt", "JWT"],
    ["saml", "SAML"],
    ["ldap", "LDAP"],
    ["active directory", "Active Directory"],

    // Data formats
    ["json", "JSON"],
    ["xml", "XML"],
    ["yaml", "YAML"],
    ["csv", "CSV"],
  ];

  const availableMap = new Map<string, string>();
  for (const ans of availableAnswers) {
    if (ans.text) {
      availableMap.set(ans.text.toLowerCase(), ans.text);
    }
  }

  const already = new Set<string>();

  // Keyword-driven matches
  for (const [keyword, answerText] of technologyKeywords) {
    const keywordLower = keyword.toLowerCase();
    const pattern =
      keyword.includes(" ") || keywordLower.length > 3
        ? keywordLower
        : `\\b${keywordLower}\\b`;
    const regex = new RegExp(pattern, "i");
    if (regex.test(codeContextLower)) {
      const found = availableMap.get(answerText.toLowerCase());
      if (found && !already.has(found)) {
        matched.push(found);
        already.add(found);
      }
    }
  }

  // Fuzzy direct mentions: look for available answers appearing as whole words
  const sortedAvailable = Array.from(availableMap.entries()).sort(
    (a, b) => b[0].length - a[0].length
  );
  for (const [ansLower, ansText] of sortedAvailable) {
    if (already.has(ansText)) continue;
    if (ansLower.length <= 2) continue;
    const regex = new RegExp(`\\b${ansLower}\\b`, "i");
    if (regex.test(codeContextLower)) {
      matched.push(ansText);
      already.add(ansText);
    }
  }

  return matched;
}

