$(document).ready(function () {
    if ($('#building-portal').length) {
        const $building = $('#pel_building');
        const $level = $('#pel_level');
        const $section = $('#pel_section');
        console.log('Portal Employee Location JS Loaded');
        
        function filterLevels() {
            const bId = $building.val();
            $level.find('option').each(function () {
                const opt = $(this);
                const match = !opt.data('building-id') || (bId && String(opt.data('building-id')) === String(bId));
                opt.toggle(match || opt.val() === '');
            });
        }

        function filterSections() {
            const lId = $level.val();
            $section.find('option').each(function () {
                const opt = $(this);
                const match = !opt.data('level-id') || (lId && String(opt.data('level-id')) === String(lId));
                opt.toggle(match || opt.val() === '');
            });
        }

        // Initial filter
        filterLevels();
        filterSections();

        $building.on('change', function () {
            $level.val('');
            $section.val('');
            filterLevels();
            filterSections();
        });

        $level.on('change', function () {
            $section.val('');
            filterSections();
        });
    }
});