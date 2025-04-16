document.addEventListener('DOMContentLoaded', function() {
    function validateCode() {
        const codeInput = document.getElementById('code');
        if (!codeInput) return true;
        
        const code = codeInput.value.trim();
        
        if (!/^[A-Za-z0-9]{6}$/.test(code)) {
            alert('提取码必须是6位字母和数字组合（区分大小写）');
            codeInput.focus();
            return false;
        }
        return true;
    }
    
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateCode()) {
                e.preventDefault();
            }
        });
    });
});