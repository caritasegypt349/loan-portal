// reusable-followup.js

// قائمة الحالات المحددة مسبقاً
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

// التحقق من الحالة المخصصة
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

// فتح المودال
function openReusableModal(recordId, pageType, currentStatus = '', currentComment = '', callback) {
  // تعيين القيم الأساسية
  document.getElementById('reusableRecordId').value = recordId;
  document.getElementById('reusablePageType').value = pageType;
  document.getElementById('reusableStatus').value = currentStatus || 'لم تتم المراجعة';
  document.getElementById('reusableComment').value = currentComment || '';
  
  // تنظيف الحقول الإضافية
  const extraFields = document.getElementById('extraFields');
  extraFields.innerHTML = '';
  
  // إضافة حقول إضافية حسب نوع الصفحة
  switch(pageType) {
    case 'review':
      // حقل القائم بالزيارة لصفحة المراجعة
      extraFields.innerHTML = `
        <div class="form-group">
          <label>القائم بالزيارة</label>
          <input type="text" id="extraVisitor" class="form-input" placeholder="اسم القائم بالزيارة">
        </div>
      `;
      break;
      
    case 'supervise':
      // بدون حقول إضافية للمتابعة
      break;
      
    case 'admin':
      // إضافة حقول إدارية متعددة
      extraFields.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
          <div class="form-group">
            <label>المراجعة الداخلية</label>
            <select id="extraReview" class="form-input">
              <option value="لم تتم المراجعة">لم تتم المراجعة</option>
              <option value="تمت المراجعة مقبول">تمت المراجعة مقبول</option>
              <option value="تمت المراجعة مرفوض">تمت المراجعة مرفوض</option>
              <!-- باقي الخيارات -->
            </select>
          </div>
          <div class="form-group">
            <label>الإدارة</label>
            <select id="extraAdmin" class="form-input">
              <option value="لم تتم المراجعة">لم تتم المراجعة</option>
              <!-- باقي الخيارات -->
            </select>
          </div>
        </div>
      `;
      break;
  }
  
  // التحقق من نوع القيمة
  checkCustomStatus();
  
  // حفظ callback الدالة الخاصة بالصفحة
  currentCallback = callback;
  
  // إظهار المودال
  document.getElementById('reusableFollowupModal').style.display = 'block';
  
  // التركيز على حقل الحالة
  setTimeout(() => {
    document.getElementById('reusableStatus').focus();
  }, 100);
}

// إغلاق المودال
function closeReusableModal() {
  document.getElementById('reusableFollowupModal').style.display = 'none';
  
  // تنظيف الحقول
  document.getElementById('reusableRecordId').value = '';
  document.getElementById('reusablePageType').value = '';
  document.getElementById('reusableStatus').value = '';
  document.getElementById('reusableComment').value = '';
  document.getElementById('customStatusIndicator').style.display = 'none';
  document.getElementById('extraFields').innerHTML = '';
  
  currentCallback = null;
}

// حفظ البيانات
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
  
  // تجميع البيانات الإضافية
  const extraData = {};
  
  switch(pageType) {
    case 'review':
      extraData.visitor = document.getElementById('extraVisitor')?.value || '';
      break;
      
    case 'admin':
      extraData.review = document.getElementById('extraReview')?.value || '';
      extraData.admin = document.getElementById('extraAdmin')?.value || '';
      break;
  }
  
  // إضافة الحالة الجديدة للقائمة إذا كانت مخصصة
  if (!predefinedStatuses.some(opt => opt.toLowerCase() === status.toLowerCase())) {
    predefinedStatuses.push(status);
    // تحديث datalist
    const datalist = document.getElementById('reusableStatusOptions');
    const newOption = document.createElement('option');
    newOption.value = status;
    datalist.appendChild(newOption);
  }
  
  // استدعاء callback الصفحة الأصلية مع البيانات
  if (currentCallback && typeof currentCallback === 'function') {
    currentCallback(recordId, status, comment, extraData);
  } else {
    console.error('لم يتم تعريف دالة الحفظ للصفحة');
  }
  
  // إغلاق المودال
  closeReusableModal();
}

// إغلاق عند النقر خارج المحتوى
document.addEventListener('DOMContentLoaded', function() {
  const modal = document.getElementById('reusableFollowupModal');
  
  if (modal) {
    modal.addEventListener('click', function(event) {
      if (event.target === modal) {
        closeReusableModal();
      }
    });
  }
  
  // إضافة حدث لإغلاق المودال بالزر ESC
  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
      closeReusableModal();
    }
  });
});

// تصدير الدوال للاستخدام في الصفحات الأخرى
window.ReusableFollowup = {
  openModal: openReusableModal,
  closeModal: closeReusableModal,
  saveFollowup: saveReusableFollowup,
  checkCustomStatus: checkCustomStatus
};