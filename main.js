const postHTML = async () => {
  // 全てのスクリプトタグを取得
  let scripts = document.querySelectorAll("script");
  let scriptsContent = "";

  // 各スクリプトタグの内容を取得
  scripts.forEach((script) => {
    if (script.src) {
      // 外部スクリプトの場合は、ソースURLを取得
      scriptsContent += `External script source: ${script.src}\n`;
    } else {
      // インラインスクリプトの場合は、その内容を取得
      scriptsContent += `${script.innerHTML}\n`;
    }
  });

  // 全てのスタイルタグとリンクタグ（スタイルシートを指しているもの）を取得
  let styleTags = document.querySelectorAll("style");
  let linkTags = document.querySelectorAll("link[rel='stylesheet']");
  let stylesContent = "";

  // インラインスタイルの内容を取得
  styleTags.forEach((style) => {
    stylesContent += `${style.innerHTML}\n`;
  });

  // 外部スタイルシートのリンクを取得
  linkTags.forEach((link) => {
    stylesContent += `External stylesheet source: ${link.href}\n`;
  });

  // ローカルホストにPOSTリクエストを送信
  const res = await fetch("http://localhost:8000/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      // 開いているページのHTML、スクリプト、スタイルを送信
      page: document.querySelector("html").innerHTML,
      scripts: scriptsContent,
      styles: stylesContent,
    }),
  });

  const data = await res.json();
  return data;
};

// モーダルを作成して表示する関数
const showModal = (content) => {
  // スタイルタグを作成
  const style = document.createElement("style");
  style.innerHTML = `
    .custom-modal {
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      z-index: 100000;
      background-color: white;
      padding: 20px;
      box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
      max-height: 80%;
      width: 80%;
      overflow-y: auto;
      font-family: 'Noto Sans JP', 'Hiragino Sans';
      line-height: 1.5;
    }
    .custom-modal button {
      display: block;
      margin: 20px auto 0;
      padding: 10px 20px;
      background-color: #007bff;
      color: white;
      border: none;
      cursor: pointer;
      border-radius: 4px;
    }
    .custom-modal button:hover {
      background-color: #0056b3;
    }
    .custom-modal .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .custom-modal .modal-header h2 {
      margin: 0;
    }
    .custom-modal .modal-content {
      margin-top: 20px;
    }
    .custom-modal .close-button {
      cursor: pointer;
      font-size: 24px;
    }
    .custom-modal h1,
    .custom-modal h2,
    .custom-modal h3,
    .custom-modal h4,
    .custom-modal h5,
    .custom-modal h6 {
      margin: 5px;
    }
    .custom-modal h1 {
      font-size: 20px;
      font-weight: 700;
    }
    .custom-modal h2 {
      font-size: 17px;
      font-weight: 600;
    }
    .custom-modal h3 {
      font-size: 16px;
      font-weight: 600;
    }
    .custom-modal h4 {
      font-size: 16px;
      font-weight: 700;
      background-color: #eee;
      color: #17194c;
      padding: 15px;
      line-height: 1.3;
    }
    .custom-modal h5 {
      font-size: 1em;
    }
    .custom-modal p {
      font-size: 12px;
      color: #000;
    }
    .custom-modal ul {
      list-style: disc;
      padding-left: 20px;
    }
    .custom-modal code {
      background-color: #f4f4f4;
      padding: 2px 4px;
      border-radius: 4px;
      color: red;
    }
    .custom-modal li {
      list-style: disc;
      font-size: 12px;
      color: #000;
      margin: 0 25px;
}
    }
  `;
  document.head.appendChild(style);

  // モーダルを作成
  const modal = document.createElement("div");
  modal.className = "custom-modal";
  modal.innerHTML = `
    <div>${content}</div>
    <button id="closeModal">閉じる</button>
  `;

  document.body.appendChild(modal);

  document.getElementById("closeModal").addEventListener("click", () => {
    modal.remove();
    style.remove();
  });
};

// ボタンを作成し、クリックイベントを設定する関数
function createButton() {
  const button = document.createElement("button");
  button.textContent = "アクセシビリティチェック開始";
  button.style.position = "fixed";
  button.style.bottom = "10px";
  button.style.left = "10px";
  button.style.zIndex = "100000";
  button.style.backgroundColor = "white";
  button.style.padding = "8px";
  return button;
}

// ボタンを作成してクリックイベントを設定
const button = createButton();
button.addEventListener("click", () => {
  postHTML().then((ret) => {
    console.log(ret); // Log the response to check its structure and data
    showModal(
      `
      <h2>アクセシビリティ評価</h2>
      <div>${ret.description}</div>
      <h3>ARIAタグの提案</h3>
      <ul>
        ${ret.aria_tags
          .map((tag) => `<li>${tag.suggested_aria_tag}</li>`)
          .join("")}
      </ul>
      <h3>Altタグがない画像</h3>
      ${ret.alt_message ? `<p>${ret.alt_message}</p>` : ""}
      <ul>
        ${ret.images_without_alt
          .map(
            (img) =>
              `<li>
                <strong>画像:</strong><br><img src="${img.src}" alt="${img.description}" style="max-width: 40%; height: auto;" /><br>
                <strong>Altタグの提案:</strong> ${img.description}
              </li>`
          )
          .join("")}
      </ul>
    `
    );
  });
});
document.body.appendChild(button);
