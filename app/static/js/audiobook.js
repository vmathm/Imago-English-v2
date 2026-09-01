document.addEventListener("DOMContentLoaded", () => {
  const audioBtn    = document.getElementById("load-audio");
  const textBtn     = document.getElementById("load-text");
  const audioInput  = document.getElementById("audio-input");
  const textInput   = document.getElementById("text-input");
  const audioPlayer = document.getElementById("audio-player");
  const textContent = document.getElementById("text-content");

  if (!textContent) {
    // Nothing to attach to – just bail out
    return;
  }


  // ==================================================
  // Suggested flashcard highlighting
  // ==================================================

  const suggestedDataEl =
    document.getElementById("suggested-flashcards-data");

  let suggestedPhrases = [];

  if (suggestedDataEl) {
    try {
      const suggestions =
        JSON.parse(suggestedDataEl.textContent);

      suggestedPhrases = suggestions
        .map(item => item.question?.trim())
        .filter(Boolean);

    } catch (err) {
      console.error(
        "Could not parse suggested flashcards:",
        err
      );
    }
  }


  function escapeRegExp(value) {
    return value.replace(
      /[.*+?^${}()|[\]\\]/g,
      "\\$&"
    );
  }


  function highlightSuggestedPhrases() {
    if (
      !textContent ||
      !suggestedPhrases.length
    ) {
      return;
    }

    /*
      Always start from the plain text.

      This also removes any previous <mark> elements,
      which means the function can safely be called
      again when a new suggestion is added.
    */
    const originalText = textContent.textContent;

    if (!originalText) {
      return;
    }

    // Longer expressions first.
    const uniquePhrases = [
      ...new Set(suggestedPhrases)
    ].sort(
      (a, b) => b.length - a.length
    );

    const pattern = uniquePhrases
      .map(escapeRegExp)
      .join("|");

    if (!pattern) {
      return;
    }

    const regex = new RegExp(
      pattern,
      "gi"
    );

    const fragment =
      document.createDocumentFragment();

    let lastIndex = 0;
    let match;

    while (
      (match = regex.exec(originalText)) !== null
    ) {
      // Normal text before the match
      if (match.index > lastIndex) {
        fragment.appendChild(
          document.createTextNode(
            originalText.slice(
              lastIndex,
              match.index
            )
          )
        );
      }

      // Highlighted suggestion
      const mark =
        document.createElement("mark");

      mark.className =
        "suggested-highlight";

      mark.textContent = match[0];

      fragment.appendChild(mark);

      lastIndex =
        match.index + match[0].length;
    }

    // Remaining text after the final match
    if (lastIndex < originalText.length) {
      fragment.appendChild(
        document.createTextNode(
          originalText.slice(lastIndex)
        )
      );
    }

    textContent.replaceChildren(fragment);
  }


  // Highlight chapter text already rendered by Flask.
  highlightSuggestedPhrases();


  // ==================================================
  // Text selection
  // ==================================================

  function toggleSelection(disabled) {
    const value = disabled ? "none" : "text";

    textContent.style.userSelect = value;
    textContent.style.touchAction =
      disabled ? "manipulation" : "auto";

    textContent.style.webkitTouchCallout =
      disabled ? "none" : "default";
  }


  toggleSelection(false);


  const isTouchDevice =
    "ontouchstart" in window ||
    navigator.maxTouchPoints > 0;


  if (isTouchDevice) {
    textContent.addEventListener(
      "contextmenu",
      e => e.preventDefault()
    );
  }


  // ==================================================
  // Local file upload
  // ==================================================

  if (audioBtn && audioInput) {
    audioBtn.addEventListener(
      "click",
      () => audioInput.click()
    );

    audioInput.addEventListener(
      "change",
      e => {
        const file = e.target.files[0];

        if (!file) return;

        audioPlayer.src =
          URL.createObjectURL(file);

        audioPlayer.style.display =
          "block";
      }
    );
  }


  if (textBtn && textInput) {
    textBtn.addEventListener(
      "click",
      () => textInput.click()
    );

    textInput.addEventListener(
      "change",
      e => {
        const file = e.target.files[0];

        if (!file) return;

        const reader = new FileReader();

        reader.onload = () => {
          try {
            const decoder =
              new TextDecoder("utf-8");

            const text =
              decoder.decode(reader.result);

            textContent.textContent = text;
            textContent.style.display =
              "block";

            // Apply suggestions after new text loads.
            highlightSuggestedPhrases();

          } catch (err) {
            console.error(
              "Error decoding text file:",
              err
            );

            textContent.textContent =
              "Erro ao ler o arquivo de texto (codificação).";

            textContent.style.display =
              "block";
          }
        };

        reader.readAsArrayBuffer(file);
      }
    );
  }


  // ==================================================
  // Selection → translation
  // ==================================================

  textContent.addEventListener(
    "mouseup",
    handleSelection
  );

  textContent.addEventListener(
    "touchend",
    handleSelection,
    { passive: true }
  );


  async function handleSelection() {
    const selection =
      window.getSelection()
        .toString()
        .trim();

    if (!selection) return;

    toggleSelection(true);

    const csrfToken = document
      .querySelector(
        'meta[name="csrf-token"]'
      )
      ?.getAttribute("content");

    try {
      const response = await fetch(
        "/audiobook/translate",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",

            ...(csrfToken
              ? {
                  "X-CSRFToken":
                    csrfToken
                }
              : {})
          },

          body: JSON.stringify({
            text: selection
          })
        }
      );

      const data = await response.json();

      if (!response.ok) {
        showFlash(
          data.error || "Translation failed. Try again.",
          "error"
        );

        return;
      }

      const { translation } = data;

      showModal(
        selection,
        translation
      );

    } catch (err) {
      console.error(
        "Translation error:",
        err
      );

      showFlash(
        "Translation failed. Try again.",
        "error"
      );

    } finally {
      toggleSelection(false);
    }

  }
  // ==================================================
  // Translation / flashcard modal
  // ==================================================

  function showModal(
    original,
    translation
  ) {
    const modal =
      document.getElementById(
        "custom-modal"
      );

    const qEl =
      document.getElementById(
        "modal-question"
      );

    const aEl =
      document.getElementById(
        "modal-answer"
      );

    const yesBtn =
      document.getElementById(
        "yesBtn"
      );

    const noBtn =
      document.getElementById(
        "noBtn"
      );

    const flipBtn =
      document.getElementById(
        "flipBtn"
      );


    // Exists only for admin +
    // activity-enabled chapter
    const suggestedBtn =
      document.getElementById(
        "add-suggested-flashcard"
      );


    toggleSelection(false);

    qEl.value = original;
    aEl.value = translation;

    modal.style.display = "block";

    setTimeout(
      () => qEl.focus(),
      0
    );


    flipBtn.onclick = () => {
      [
        qEl.value,
        aEl.value
      ] = [
        aEl.value,
        qEl.value
      ];

      qEl.focus();
    };


    // Normal flashcard
    yesBtn.onclick = () => {
      const question =
        qEl.value.trim();

      const answer =
        aEl.value.trim();

      if (!question || !answer) {
        showFlash(
          "Both question and answer are required.",
          "error"
        );

        return;
      }

      addFlashcard(
        question,
        answer
      );

      modal.style.display =
        "none";

      toggleSelection(false);
    };


    // Suggested flashcard
    if (suggestedBtn) {
      suggestedBtn.onclick =
        async () => {

          const question =
            qEl.value.trim();

          const answer =
            aEl.value.trim();

          if (!question || !answer) {
            showFlash(
              "Both question and answer are required.",
              "error"
            );

            return;
          }

          await addSuggestedFlashcard(
            question,
            answer,
            suggestedBtn
          );
        };
    }


    noBtn.onclick = () => {
      modal.style.display = "none";
      toggleSelection(false);
    };


    window.onclick = evt => {
      if (evt.target === modal) {
        modal.style.display =
          "none";

        toggleSelection(false);
      }
    };
  }


  // ==================================================
  // Add normal flashcard
  // ==================================================

  async function addFlashcard(
    question,
    answer
  ) {
    const formData =
      new FormData();

    formData.append(
      "question",
      question
    );

    formData.append(
      "answer",
      answer
    );


    const csrfToken = document
      .querySelector(
        'meta[name="csrf-token"]'
      )
      ?.getAttribute("content");


    try {
      const response = await fetch(
        "/flashcard/addcards",
        {
          method: "POST",

          headers: {
            ...(csrfToken
              ? {
                  "X-CSRFToken":
                    csrfToken
                }
              : {}),

            "X-Requested-With":
              "XMLHttpRequest"
          },

          body: formData
        }
      );


      // Inactive user → HTML 403 response
      if (response.status === 403) {
        const html =
          await response.text();

        document.open();
        document.write(html);
        document.close();

        return;
      }


      const result =
        await response.json();


      showFlash(
        result.message ||
          "Unexpected response.",

        result.status === "success"
          ? "success"
          : "error"
      );

    } catch (err) {
      console.error(
        "Error adding flashcard from audiobook.js:",
        err
      );

      showFlash(
        "Erro ao adicionar o flashcard. Tente novamente.",
        "error"
      );
    }
  }


  // ==================================================
  // Add suggested flashcard
  // ==================================================

  async function addSuggestedFlashcard(
    question,
    answer,
    button
  ) {
    const csrfToken = document
      .querySelector(
        'meta[name="csrf-token"]'
      )
      ?.getAttribute("content");


    const url =
      button.dataset.url;


    if (!url) {
      console.error(
        "Suggested flashcard button has no data-url."
      );

      showFlash(
        "Could not add suggested flashcard.",
        "error"
      );

      return;
    }


    button.disabled = true;


    try {
      const response =
        await fetch(
          url,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",

              ...(csrfToken
                ? {
                    "X-CSRFToken":
                      csrfToken
                  }
                : {})
            },

            body: JSON.stringify({
              question,
              answer
            })
          }
        );


      const result =
        await response.json();


      if (!response.ok) {
        showFlash(
          result.message ||
            "Could not add suggested flashcard.",
          "error"
        );

        return;
      }


      showFlash(
        result.message ||
          "Suggested flashcard added.",
        "success"
      );


      /*
        Add the newly created suggestion to
        the current highlighting set immediately,
        so admin does not need to reload the chapter.
      */
      if (
        question &&
        !suggestedPhrases.includes(question)
      ) {
        suggestedPhrases.push(question);

        highlightSuggestedPhrases();
      }


      const modal =
        document.getElementById(
          "custom-modal"
        );

      modal.style.display =
        "none";

      toggleSelection(false);

    } catch (err) {
      console.error(
        "Error adding suggested flashcard:",
        err
      );

      showFlash(
        "Could not add suggested flashcard.",
        "error"
      );

    } finally {
      button.disabled = false;
    }
  }


  // ==================================================
  // Flash messages
  // ==================================================

  function showFlash(
    msg,
    kind = "success"
  ) {
    const flashDiv =
      document.createElement("div");

    flashDiv.className =
      `flashcard-${kind}-message`;

    flashDiv.textContent = msg;


    const container =
      document.getElementById(
        "flash-message-container"
      );


    if (!container) {
      console.warn(
        "flash-message-container not found."
      );

      return;
    }


    container.appendChild(
      flashDiv
    );


    setTimeout(
      () => flashDiv.remove(),
      3000
    );
  }


  // ==================================================
  // Delete suggested flashcard
  // ==================================================

  document.addEventListener(
    "click",
    async evt => {

      const button =
        evt.target.closest(
          ".delete-suggested-flashcard"
        );

      if (!button) return;


      const cardElement =
        button.closest(
          ".suggested-flashcard-item"
        );


      const csrfToken = document
        .querySelector(
          'meta[name="csrf-token"]'
        )
        ?.getAttribute("content");


      button.disabled = true;


      try {
        const response =
          await fetch(
            button.dataset.url,
            {
              method: "POST",

              headers: {
                ...(csrfToken
                  ? {
                      "X-CSRFToken":
                        csrfToken
                    }
                  : {})
              }
            }
          );


        const result =
          await response.json();


        if (!response.ok) {
          showFlash(
            result.message ||
              "Could not delete suggested flashcard.",
            "error"
          );

          return;
        }


        cardElement?.remove();


        showFlash(
          result.message ||
            "Suggested flashcard deleted.",
          "success"
        );


        /*
          Reloading here is not necessary.
          The database is correct immediately.

          Highlight removal can be added later
          if we want the authoring screen to update
          completely without refresh.
        */

      } catch (err) {
        console.error(
          "Error deleting suggested flashcard:",
          err
        );

        showFlash(
          "Could not delete suggested flashcard.",
          "error"
        );

      } finally {
        button.disabled = false;
      }
    }
  );


  // ==================================================
  // Bulk-add selected suggested flashcards
  // ==================================================

  const addSelectedBtn =
    document.getElementById(
      "add-selected-suggested-flashcards"
    );


  if (addSelectedBtn) {
    addSelectedBtn.addEventListener(
      "click",
      async () => {

        const selectedIds =
          Array.from(
            document.querySelectorAll(
              ".suggested-flashcard-checkbox:checked"
            )
          ).map(
            checkbox =>
              checkbox.value
          );


        if (!selectedIds.length) {
          showFlash(
            "Select at least one flashcard.",
            "error"
          );

          return;
        }


        const csrfToken = document
          .querySelector(
            'meta[name="csrf-token"]'
          )
          ?.getAttribute("content");


        addSelectedBtn.disabled =
          true;


        try {
          const response =
            await fetch(
              addSelectedBtn.dataset.url,
              {
                method: "POST",

                headers: {
                  "Content-Type":
                    "application/json",

                  ...(csrfToken
                    ? {
                        "X-CSRFToken":
                          csrfToken
                      }
                    : {})
                },

                body: JSON.stringify({
                  card_ids:
                    selectedIds
                })
              }
            );


          const result =
            await response.json();


          if (!response.ok) {
            showFlash(
              result.message ||
                "Could not add flashcards.",
              "error"
            );

            return;
          }


          showFlash(
            result.message ||
              "Flashcards added.",
            "success"
          );


          /*
            Prevent immediate re-adding
            from the same page.
          */
          document
            .querySelectorAll(
              ".suggested-flashcard-checkbox:checked"
            )
            .forEach(
              checkbox => {
                checkbox.checked =
                  false;
              }
            );


        } catch (err) {
          console.error(
            "Error adding suggested flashcards:",
            err
          );

          showFlash(
            "Could not add flashcards.",
            "error"
          );

        } finally {
          addSelectedBtn.disabled =
            false;
        }
      }
    );
  }
});