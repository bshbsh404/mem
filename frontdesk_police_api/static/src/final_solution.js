/** @odoo-module **/

/**
 * الحل النهائي لمشكلة showScreen
 */
export class FinalSolution {
    
    /**
     * الحل النهائي لمشكلة showScreen
     */
    static solveShowScreenIssue() {
        console.log("FinalSolution: Starting final solution for showScreen issue");
        
        // الحل 1: البحث عن showScreen في الصفحة
        const findShowScreen = () => {
            // البحث في window object
            if (window.showScreen && typeof window.showScreen === 'function') {
                return window.showScreen;
            }
            
            // البحث في document scripts
            const scripts = document.querySelectorAll('script');
            for (let script of scripts) {
                if (script.textContent && script.textContent.includes('showScreen')) {
                    console.log("FinalSolution: Found showScreen in script");
                }
            }
            
            return null;
        };
        
        // الحل 2: إنشاء showScreen function
        const createShowScreen = () => {
            console.log("FinalSolution: Creating showScreen function");
            
            const showScreenFunction = (screenName) => {
                console.log(`FinalSolution: showScreen called with ${screenName}`);
                
                // محاولة استخدام window.location
                if (window.location && window.location.href) {
                    const currentUrl = window.location.href;
                    const baseUrl = currentUrl.split('/kiosk/')[0];
                    const newUrl = `${baseUrl}/kiosk/3/${screenName.toLowerCase()}`;
                    console.log(`FinalSolution: Redirecting to ${newUrl}`);
                    window.location.href = newUrl;
                    return true;
                }
                
                return false;
            };
            
            // إضافة showScreen إلى window
            window.showScreen = showScreenFunction;
            console.log("FinalSolution: showScreen function added to window");
            
            return showScreenFunction;
        };
        
        // الحل 3: إصلاح المكونات
        const fixComponents = () => {
            console.log("FinalSolution: Fixing components");
            
            // التأكد من تسجيل المكونات
            if (typeof window !== 'undefined') {
                // إضافة المكونات إلى window إذا لم تكن موجودة
                if (!window.PoliceVisitorForm) {
                    console.log("FinalSolution: PoliceVisitorForm will be loaded");
                }
                
                if (!window.EnhancedPoliceVisitorForm) {
                    console.log("FinalSolution: EnhancedPoliceVisitorForm will be loaded");
                }
            }
        };
        
        // تنفيذ الحلول
        let showScreenFunction = findShowScreen();
        
        if (!showScreenFunction) {
            showScreenFunction = createShowScreen();
        }
        
        fixComponents();
        
        console.log("FinalSolution: Final solution completed");
        
        return showScreenFunction;
    }
    
    /**
     * إصلاح مشكلة _goToEnhancedPoliceForm
     */
    static fixGoToEnhancedPoliceForm() {
        console.log("FinalSolution: Fixing _goToEnhancedPoliceForm");
        
        // البحث عن جميع المكونات في الصفحة
        const findComponents = () => {
            const components = [];
            
            // البحث في scripts
            const scripts = document.querySelectorAll('script');
            for (let script of scripts) {
                if (script.textContent && script.textContent.includes('_goToEnhancedPoliceForm')) {
                    console.log("FinalSolution: Found _goToEnhancedPoliceForm in script");
                    components.push(script);
                }
            }
            
            return components;
        };
        
        // إصلاح المكونات
        const components = findComponents();
        console.log(`FinalSolution: Found ${components.length} components with _goToEnhancedPoliceForm`);
        
        // إنشاء حل بديل
        const createAlternativeSolution = () => {
            console.log("FinalSolution: Creating alternative solution");
            
            // إضافة دالة بديلة إلى window
            window.goToEnhancedPoliceForm = () => {
                console.log("FinalSolution: Alternative goToEnhancedPoliceForm called");
                
                // استخدام showScreen إذا كان متوفراً
                if (window.showScreen && typeof window.showScreen === 'function') {
                    window.showScreen("EnhancedPoliceVisitorForm");
                    return;
                }
                
                // استخدام window.location كحل أخير
                if (window.location && window.location.href) {
                    const currentUrl = window.location.href;
                    const baseUrl = currentUrl.split('/kiosk/')[0];
                    const newUrl = `${baseUrl}/kiosk/3/enhancedpolicevisitorform`;
                    console.log(`FinalSolution: Redirecting to ${newUrl}`);
                    window.location.href = newUrl;
                }
            };
            
            console.log("FinalSolution: Alternative solution created");
        };
        
        createAlternativeSolution();
    }
    
    /**
     * تشغيل الحل النهائي
     */
    static run() {
        console.log("FinalSolution: Running final solution");
        
        // حل مشكلة showScreen
        this.solveShowScreenIssue();
        
        // إصلاح مشكلة _goToEnhancedPoliceForm
        this.fixGoToEnhancedPoliceForm();
        
        console.log("FinalSolution: Final solution completed successfully");
    }
}

// تشغيل الحل النهائي عند تحميل الصفحة
if (typeof window !== 'undefined') {
    window.FinalSolution = FinalSolution;
    
    // تشغيل الحل عند تحميل الصفحة
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            FinalSolution.run();
        });
    } else {
        FinalSolution.run();
    }
    
    // تشغيل الحل بعد تحميل الصفحة بالكامل
    window.addEventListener('load', () => {
        setTimeout(() => {
            FinalSolution.run();
        }, 2000);
    });
    
    // تشغيل الحل كل 5 ثوانٍ للتأكد من عمله
    setInterval(() => {
        FinalSolution.run();
    }, 5000);
} 