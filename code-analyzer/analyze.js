const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

// Путь к корню проекта
const PROJECT_PATH = 'C:\\Users\\Andrew\\kolybel_core';
// Форматы файлов для анализа
const FILE_EXTENSIONS = ['.js', '.jsx', '.ts', '.tsx', '.json', '.css', '.html'];

// Рекурсивный обход файлов
function walkSync(currentDirPath, callback) {
  fs.readdirSync(currentDirPath).forEach((name) => {
    const filePath = path.join(currentDirPath, name);
    const stat = fs.statSync(filePath);
    if (stat.isFile()) {
      callback(filePath, stat);
    } else if (stat.isDirectory()) {
      walkSync(filePath, callback);
    }
  });
}

// Сканируем проект
const files = [];
walkSync(PROJECT_PATH, (filePath) => {
  const ext = path.extname(filePath);
  if (FILE_EXTENSIONS.includes(ext)) {
    files.push(filePath);
  }
});

console.log(`Найдено файлов для анализа: ${files.length}`);

// Отправка в Ollama
files.forEach((file) => {
  fs.readFile(file, 'utf8', (err, data) => {
    if (err) {
      console.error(`Ошибка чтения файла ${file}:`, err);
      return;
    }

    const prompt = `
Ты — эксперт по разработке программного обеспечения.
Проанализируй следующий код и найди:
- Возможные баги или проблемы
- Нарушения лучшей практики
- Возможные утечки памяти
- Проблемы с производительностью
- Ошибки типизации (если TypeScript)
- Предложи оптимизацию или рефакторинг

Код:
\`\`\`${path.extname(file).slice(1)}
${data}
\`\`\`
`;

    const command = `ollama run deepseek-coder`;
    const child = exec(command);

    let inputSent = false;

    child.stdin.write(prompt + '\n');
    child.stdin.end();

    child.stdout.on('data', (data) => {
      console.log(`\n\n=== АНАЛИЗ ФАЙЛА: ${file} ===\n`);
      process.stdout.write(data.toString());
    });

    child.stderr.on('data', (data) => {
      console.error(`Ошибка при выполнении модели для ${file}:`, data.toString());
    });
  });
});