// reusable-followup.js
// مكوّن قابل لإعادة الاستخدام لتحديث حالة/تعليق المتابعة.
// يحقن الـ HTML والـ CSS الخاصين به تلقائيًا في الصفحة، فيكفي عمل:
//   <script src="reusable-followup.js"></script>
// بدون الحاجة لنسخ أي HTML يدويًا في كل صفحة (وده اللي كان بيسبب تعارضات لو اتنسخ أكتر من مرة).

(function () {
  'use strict';

  // ✅ مصدر واحد لقائمة الحالات (بدل ما كانت مكررة في HTML وفي JS)
  const predefinedStatuses = [
    "لم تتم المراجعة",
    "الموقع لاستكمال الموافقة علي تمويل العميل",
    "تمت المراجعة مقبول",
    "تمت الموافقة على التمويل، وتم تعديل المبلغ/المدة",
    "تمت المراجعة مرفوض",
    "تم الغاء الطلب من العميل",
    "مطلوب ارسال الملف على الميل",
    "مرسل ميل بالملاحظات فى انتظار الرد",
    "مناقشه المبلغ",
    "مطلوب تغيير الضامن",
    "مطلوب عمل استثناء الـ iScore",
    "عدد القروض الموجودة للعميل أكبر من الحد المسموح به (Exceeded Limit)",
    "تاريخ الاستعلام الخاص بالعميل قديم. يرجى عمل استعلام جديد، حيث لا يعتد بالاستعلام الحالي",
    "يرجى استكمال باقى الملاحظات الموجودة لاتمام عمليه المراجعة و الموافقه",
    "سداد معجل",
    "مرفوض من اداره الائتمان"
  ];

  let currentCallback = null;
  let injected = false;

  // ========== حقن الـ CSS ==========
  function injectStyles() {
    if (document.getElementById('reusableFollowupStyles')) return;
    const style = document.createElement('style');
    style.id = 'reusableFollowupStyles';
    style.textContent = `
      .followup-modal { display: none; position: fixed; z-index: 2000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); }
      .followup-modal .modal-content { background: white; margin: 5% auto; padding: 20px; width: 90%; max-width: 500px; border-radius: 8px; max-height: 90vh; overflow-y: auto; }
      .followup-modal .close { float: left; font-size: 24px; cursor: pointer; color: #999; }
      .followup-modal .close:hover { color: #e74c3c; }
      .followup-modal .form-group { margin-bottom: 20px; }
      .followup-modal .form-input {
        width: 100%; padding: 12px; border: 2px solid #3498db; border-radius: 6px;
        font-size: 14px; transition: all 0.3s; box-sizing: border-box;
      }
      .followup-modal .form-input:focus {
        border-color: #2ecc71; box-shadow: 0 0 0 3px rgba(46, 204, 113, 0.2); outline: none;
      }
      .followup-modal .form-textarea {
        width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 6px;
        font-size: 14px; resize: vertical; min-height: 100px; box-sizing: border-box;
      }
      .followup-modal .custom-indicator {
        display: none; margin-top: 5px; padding: 5px 10px; background-color: #e8f6e8;
        border: 1px solid #2ecc71; border-radius: 4px; color: #27ae60; font-size: 12px;
      }
      .followup-modal .hint { color: #666; font-weight: normal; font-size: 12px; }
      .followup-modal .modal-actions {
        display: flex; justify-content: flex-start; gap: 10px; margin-top: 25px;
        padding-top: 20px; border-top: 1px solid #eee;
      }
      .followup-modal .btn { padding: 12px 25px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: bold; transition: all 0.3s; }
      .followup-modal .btn-primary { background-color: #2ecc71; color: white; }
      .followup-modal .btn-primary:hover { background-color: #27ae60; transform: translateY(-2px); }
      .followup-modal .btn-secondary { background-color: #95a5a6; color: white; }
      .followup-modal .btn-secondary:hover { background-color: #7f8c8d; }
    `;
    document.head.appendChild(style);
  }

  // ========== حقن الـ HTML ==========
  function injectMarkup() {
    if (document.getElementById('reusableFollowupModal')) return; // منع الحقن المزدوج
    const wrapper = document.createElement('div');
    wrapper.innerHTML = `
      <div id="reusableFollowupModal" class="modal followup-modal">
        <div class="modal-content">
          <span class="close" data-action="close">&times;</span>
          <h3>تعديل متابعة العملية</h3>

          <div class="form-group">
            <label>حالة المتابعة <small class="hint">(اختر من القائمة أو اكتب جديداً)</small></label>
            <input
              type="text"
              id="reusableStatus"
              list="reusableStatusOptions"
              placeholder="اختر أو اكتب حالة جديدة..."
              class="form-input"
            />
            <datalist id="reusableStatusOptions"></datalist>
            <div id="customStatusIndicator" class="custom-indicator">
              <span>✓ حالة مخصصة</span>
            </div>
          </div>

          <div class="form-group">
            <label>تعليق المتابعة <small class="hint">(التفاصيل والملاحظات الإضافية)</small></label>
            <textarea id="reusableComment" rows="4" placeholder="اكتب تعليق المتابعة هنا..." class="form-textarea"></textarea>
          </div>

          <div id="extraFields"></div>

          <input type="hidden" id="reusableRecordId" />
          <input type="hidden" id="reusablePageType" />

          <div class="modal-actions">
            <button type="button" data-action="save" class="btn btn-primary">💾 حفظ التغييرات</button>
            <button type="button" data-action="close" class="btn btn-secondary">✕ إلغاء</button>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(wrapper.firstElementChild);

    // ربط الأحداث بدل onclick/oninput inline
    const modal = document.getElementById('reusableFollowupModal');
    modal.querySelectorAll('[data-action="close"]').forEach(el => el.addEventListener('click', closeReusableModal));
    modal.querySelector('[data-action="save"]').addEventListener('click', saveReusableFollowup);
    document.getElementById('reusableStatus').addEventListener('input', checkCustomStatus);

    modal.addEventListener('click', function (event) {
      if (event.target === modal) closeReusableModal();
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') closeReusableModal();
    });

    populateStatusOptions();
  }

  function populateStatusOptions() {
    const datalist = document.getElementById('reusableStatusOptions');
    if (!datalist) return;
    datalist.innerHTML = '';
    predefinedStatuses.forEach(status => {
      const opt = document.createElement('option');
      opt.value = status;
      datalist.appendChild(opt);
    });
  }

  function ensureInjected() {
    if (injected) return;
    injectStyles();
    injectMarkup();
    injected = true;
  }

  // ========== التحقق من الحالة المخصصة ==========
  function checkCustomStatus() {
    const statusField = document.getElementById('reusableStatus');
    const indicator = document.getElementById('customStatusIndicator');
    const value = statusField.value.trim();

    if (!value) {
      indicator.style.display = 'none';
      return;
    }

    const isPredefined = predefinedStatuses.some(option =>
      option.toLowerCase() === value.toLowerCase()
    );

    if (isPredefined) {
      indicator.style.display = 'none';
      statusField.style.borderColor = '#3498db';
      statusField.style.background = '#f8f9fa';
    } else {
      indicator.style.display = 'block';
      statusField.style.borderColor = '#2ecc71';
      statusField.style.background = '#f0fff4';
    }
  }

  // ========== فتح المودال ==========
  function openReusableModal(recordId, pageType, currentStatus, currentComment, callback) {
    ensureInjected();

    document.getElementById('reusableRecordId').value = recordId;
    document.getElementById('reusablePageType').value = pageType;
    document.getElementById('reusableStatus').value = currentStatus || 'لم تتم المراجعة';
    document.getElementById('reusableComment').value = currentComment || '';

    const extraFields = document.getElementById('extraFields');
    extraFields.innerHTML = '';

    if (pageType === 'review') {
      extraFields.innerHTML = `
        <div class="form-group">
          <label>القائم بالزيارة</label>
          <input type="text" id="extraVisitor" class="form-input" placeholder="اسم القائم بالزيارة">
        </div>
      `;
    } else if (pageType === 'admin') {
      const statusOptionsHtml = predefinedStatuses.map(s => `<option value="${escapeHtml(s)}">${escapeHtml(s)}</option>`).join('');
      extraFields.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
          <div class="form-group">
            <label>المراجعة الداخلية</label>
            <select id="extraReview" class="form-input">${statusOptionsHtml}</select>
          </div>
          <div class="form-group">
            <label>الإدارة</label>
            <select id="extraAdmin" class="form-input">${statusOptionsHtml}</select>
          </div>
        </div>
      `;
    }
    // pageType === 'supervise' -> بدون حقول إضافية

    checkCustomStatus();
    currentCallback = typeof callback === 'function' ? callback : null;

    document.getElementById('reusableFollowupModal').style.display = 'block';

    setTimeout(() => {
      const statusField = document.getElementById('reusableStatus');
      if (statusField) statusField.focus();
    }, 100);
  }

  // ========== إغلاق المودال ==========
  function closeReusableModal() {
    const modal = document.getElementById('reusableFollowupModal');
    if (!modal) return;
    modal.style.display = 'none';

    document.getElementById('reusableRecordId').value = '';
    document.getElementById('reusablePageType').value = '';
    document.getElementById('reusableStatus').value = '';
    document.getElementById('reusableComment').value = '';
    document.getElementById('customStatusIndicator').style.display = 'none';
    document.getElementById('extraFields').innerHTML = '';

    currentCallback = null;
  }

  // ========== حفظ البيانات ==========
  function saveReusableFollowup() {
    const recordId = document.getElementById('reusableRecordId').value;
    const pageType = document.getElementById('reusablePageType').value;
    const status = document.getElementById('reusableStatus').value.trim();
    const comment = document.getElementById('reusableComment').value.trim();

    if (!status) {
      alert('الرجاء إدخال حالة المتابعة');
      document.getElementById('reusableStatus').focus();
      return;
    }

    const extraData = {};
    if (pageType === 'review') {
      const visitorEl = document.getElementById('extraVisitor');
      extraData.visitor = visitorEl ? visitorEl.value : '';
    } else if (pageType === 'admin') {
      const reviewEl = document.getElementById('extraReview');
      const adminEl = document.getElementById('extraAdmin');
      extraData.review = reviewEl ? reviewEl.value : '';
      extraData.admin = adminEl ? adminEl.value : '';
    }

    if (!predefinedStatuses.some(opt => opt.toLowerCase() === status.toLowerCase())) {
      predefinedStatuses.push(status);
      populateStatusOptions();
    }

    if (currentCallback) {
      currentCallback(recordId, status, comment, extraData);
    } else {
      console.error('لم يتم تعريف دالة الحفظ (callback) لهذا الاستدعاء');
    }

    closeReusableModal();
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ========== تصدير الدوال للاستخدام في الصفحات الأخرى ==========
  window.ReusableFollowup = {
    openModal: openReusableModal,
    closeModal: closeReusableModal,
    saveFollowup: saveReusableFollowup,
    checkCustomStatus: checkCustomStatus,
    getStatuses: () => predefinedStatuses.slice()
  };
})();
