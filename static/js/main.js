document.addEventListener('DOMContentLoaded', function() {
    const invoiceKeysTextarea = document.getElementById('invoice_keys');
    const validCountBadge = document.getElementById('validCount');
    const invalidCountBadge = document.getElementById('invalidCount');
    const submitBtn = document.getElementById('submitBtn');
    const form = document.getElementById('keysForm');

    // Function to validate invoice key
    function isValidInvoiceKey(key) {
        // Remove all non-digit characters
        const cleanKey = key.replace(/\D/g, '');
        // Check if it has exactly 44 digits
        return cleanKey.length === 44;
    }

    // Function to update key counts
    function updateKeyCounts() {
        const text = invoiceKeysTextarea.value.trim();
        if (!text) {
            validCountBadge.textContent = '0';
            invalidCountBadge.textContent = '0';
            return;
        }

        const lines = text.split('\n').filter(line => line.trim());
        let validCount = 0;
        let invalidCount = 0;

        lines.forEach(line => {
            const key = line.trim();
            if (key) {
                if (isValidInvoiceKey(key)) {
                    validCount++;
                } else {
                    invalidCount++;
                }
            }
        });

        validCountBadge.textContent = validCount;
        invalidCountBadge.textContent = invalidCount;

        // Update badge colors
        validCountBadge.className = validCount > 0 ? 'badge bg-success' : 'badge bg-secondary';
        invalidCountBadge.className = invalidCount > 0 ? 'badge bg-warning' : 'badge bg-secondary';

        // Enable/disable submit button
        submitBtn.disabled = validCount === 0;
    }

    // Add event listener for textarea changes
    invoiceKeysTextarea.addEventListener('input', updateKeyCounts);
    invoiceKeysTextarea.addEventListener('paste', function() {
        // Update counts after paste with slight delay
        setTimeout(updateKeyCounts, 100);
    });

    // Form submission handling
    form.addEventListener('submit', function(e) {
        const text = invoiceKeysTextarea.value.trim();
        if (!text) {
            e.preventDefault();
            alert('Por favor, insira pelo menos uma chave de nota fiscal.');
            return;
        }

        const lines = text.split('\n').filter(line => line.trim());
        const validKeys = lines.filter(line => isValidInvoiceKey(line.trim()));

        if (validKeys.length === 0) {
            e.preventDefault();
            alert('Nenhuma chave válida encontrada. Chaves devem ter exatamente 44 dígitos.');
            return;
        }

        // Change button text to show processing
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Iniciando...';
        submitBtn.disabled = true;
    });

    // Auto-format keys on paste
    invoiceKeysTextarea.addEventListener('paste', function(e) {
        setTimeout(function() {
            const text = invoiceKeysTextarea.value;
            const lines = text.split('\n');
            const formattedLines = lines.map(line => {
                const cleanLine = line.trim();
                // Remove any non-digit characters and format if it looks like an invoice key
                const digitsOnly = cleanLine.replace(/\D/g, '');
                if (digitsOnly.length === 44) {
                    return digitsOnly;
                }
                return cleanLine;
            });
            
            invoiceKeysTextarea.value = formattedLines.join('\n');
            updateKeyCounts();
        }, 100);
    });

    // Initial count update
    updateKeyCounts();

    // Add tooltips to help icons
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add sample data functionality (for testing)
    function addSampleData() {
        const sampleKeys = [
            '12345678901234567890123456789012345678901234',
            '98765432109876543210987654321098765432109876',
            '11111111111111111111111111111111111111111111',
            '22222222222222222222222222222222222222222222'
        ];
        
        invoiceKeysTextarea.value = sampleKeys.join('\n');
        updateKeyCounts();
    }

    // Add keyboard shortcut for sample data (Ctrl+Shift+S)
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.shiftKey && e.key === 'S') {
            e.preventDefault();
            addSampleData();
        }
    });
});
