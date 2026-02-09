import introJs from 'intro.js'
import 'intro.js/introjs.css'
import '../assets/intro-custom.css'

const TOUR_COMPLETED_KEY = 'veriflow-tour-completed'

type Position = 'top' | 'bottom' | 'left' | 'right' | 'floating'

interface TourStepDef {
    selector: string
    title: string
    intro: string
    position?: Position
}

function buildSteps() {
    const steps: { element: HTMLElement; title: string; intro: string; position: Position }[] = []

    const stepDefs: TourStepDef[] = [
        {
            selector: '[data-tour="header"]',
            title: '🎉 Welcome to VeriFlow',
            intro: 'Your <strong>Autonomous Research Reproducibility Engineer</strong>. This guided tour will walk you through all major features of the application. Let\'s get started!',
            position: 'bottom',
        },
        {
            selector: '[data-tour="upload-panel"]',
            title: '📁 Upload Publication',
            intro: 'Start here by <strong>uploading a research paper</strong> (PDF). VeriFlow\'s AI agents will extract the experimental design automatically.',
            position: 'right',
        },
        {
            selector: '[data-tour="pdf-upload-zone"]',
            title: '📄 Drag & Drop Your PDF',
            intro: 'Simply drag and drop your research paper here, or click to browse. VeriFlow supports PDF files containing scientific publications.',
            position: 'right',
        },
        {
            selector: '[data-tour="load-demo"]',
            title: '🧪 Try the Demo',
            intro: 'New here? Click <strong>"Load MAMA-MIA Demo"</strong> to instantly load a pre-built breast cancer MRI segmentation example — no PDF required. <br><br><em>The tour will automatically click this button for you in the next step.</em>',
            position: 'right',
        },
        {
            selector: '[data-tour="study-design"]',
            title: '📋 Review Study Design',
            intro: 'After uploading, the Scholar AI agent extracts an <strong>ISA hierarchy</strong> (Investigation → Study → Assay) from your paper. Review, edit, and select an assay here.',
            position: 'right',
        },
        {
            selector: '[data-tour="investigation-field"]',
            title: '🔬 Investigation',
            intro: 'The <strong>Investigation</strong> represents the overall research project. You can click on it to view and edit its properties in the panel below.',
            position: 'right',
        },
        {
            selector: '[data-tour="study-field"]',
            title: '📊 Study',
            intro: 'A <strong>Study</strong> is a specific component of the investigation. Click to view details like study design, number of subjects, and description.',
            position: 'right',
        },
        {
            selector: '[data-tour="assay-field"]',
            title: '⚗️ Assay (Clickable!)',
            intro: '<strong>Assays</strong> are the experimental workflows within a study. <strong>Click on an assay</strong> to select it and view its workflow steps. This is a crucial step for workflow assembly!',
            position: 'right',
        },
        {
            selector: '[data-tour="assemble-button"]',
            title: '🔧 Assemble Workflow',
            intro: 'Once you\'ve selected an assay, click <strong>"Assemble Selected Assay"</strong> to generate a reproducible CWL workflow. The Engineer AI agent will create the workflow graph.',
            position: 'top',
        },
        {
            selector: '[data-tour="workflow-canvas"]',
            title: '🎨 Workflow Canvas',
            intro: 'The assembled workflow appears here as an <strong>interactive graph</strong> with tool nodes, data nodes, and connections. You can explore the workflow structure visually.',
            position: 'left',
        },
        {
            selector: '[data-tour="run-workflow-button"]',
            title: '▶️ Run Workflow',
            intro: 'Click <strong>"Run Workflow"</strong> to execute the assembled workflow. VeriFlow will process the data and generate results.',
            position: 'bottom',
        },
        {
            selector: '[data-tour="console"]',
            title: '💻 Agent Console',
            intro: 'Real-time logs from <strong>Scholar, Engineer, and Reviewer</strong> AI agents appear here. Monitor orchestration progress, view generated code, and debug issues.',
            position: 'top',
        },
        {
            selector: '[data-tour="output-measurements-card"]',
            title: '📊 Output Measurements',
            intro: 'After workflow execution, click on an <strong>Output Measurements</strong> card to view the results in the right panel.',
            position: 'left',
        },
        {
            selector: '[data-tour="results-panel"]',
            title: '📁 Visualize & Export Results',
            intro: 'After running the workflow, <strong>view outputs and export results</strong> from this panel. You can browse datasets and download SDS-compliant packages.',
            position: 'left',
        },
        {
            selector: '[data-tour="nii-file"]',
            title: '🧠 View .nii Files',
            intro: 'Click on <strong>.nii files</strong> to visualize medical imaging data in the VolView viewer. Perfect for MRI, CT scans, and other neuroimaging formats.',
            position: 'left',
        },
    ]

    for (const def of stepDefs) {
        const el = document.querySelector(def.selector)
        if (el) {
            steps.push({
                element: el as HTMLElement,
                title: def.title,
                intro: def.intro,
                position: def.position || 'bottom',
            })
        }
    }

    return steps
}

export function useTour() {
    function startTour() {
        // Small delay to ensure DOM elements are rendered
        setTimeout(() => {
            const steps = buildSteps()
            if (steps.length === 0) {
                console.warn('No tour steps found. Make sure data-tour attributes are present.')
                return
            }

            const tour = introJs()
            tour.setOptions({
                steps,
                showProgress: true,
                showBullets: true,
                exitOnOverlayClick: false,
                disableInteraction: false,
                scrollToElement: true,
                scrollPadding: 30,
                overlayOpacity: 0.5,
                nextLabel: 'Next →',
                prevLabel: '← Back',
                doneLabel: '🎉 Done!',
                skipLabel: '×',
                tooltipClass: 'veriflow-tour-tooltip',
                highlightClass: 'veriflow-tour-highlight',
            })

            // Add event handlers for interactive tour steps
            tour.onbeforechange(function () {
                // Future: Add interactive behaviors here
                return true
            })

            tour.onchange(function (targetElement: HTMLElement) {
                // Scroll the target element into view with some padding
                if (targetElement) {
                    targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
                }
            })

            tour.oncomplete(() => {
                localStorage.setItem(TOUR_COMPLETED_KEY, 'true')
                console.log('✅ Tour completed!')
            })

            tour.onexit(() => {
                localStorage.setItem(TOUR_COMPLETED_KEY, 'true')
                console.log('👋 Tour exited')
            })

            tour.start()
        }, 500) // Increased delay to ensure all elements are loaded
    }

    function startTourIfFirstVisit() {
        if (!localStorage.getItem(TOUR_COMPLETED_KEY)) {
            startTour()
        }
    }

    function resetTour() {
        localStorage.removeItem(TOUR_COMPLETED_KEY)
        console.log('🔄 Tour reset - will show on next page load')
    }

    return {
        startTour,
        startTourIfFirstVisit,
        resetTour,
    }
}
