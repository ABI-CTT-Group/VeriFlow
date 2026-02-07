import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import UploadModule from '../UploadModule.vue'

describe('UploadModule.vue', () => {
    beforeEach(() => {
        setActivePinia(createPinia())
    })

    const mountComponent = (props = {}) => {
        return mount(UploadModule, {
            props,
            global: {
                stubs: {
                    Upload: { template: '<span />' },
                    File: { template: '<span />' },
                    X: { template: '<span />' },
                    ChevronDown: { template: '<span />' },
                    ChevronRight: { template: '<span />' },
                    ChevronLeft: { template: '<span />' },
                    Loader2: { template: '<span />' },
                    Beaker: { template: '<span />' },
                    FileText: { template: '<span />' },
                    Plus: { template: '<span />' },
                },
            },
        })
    }

    it('renders correctly', () => {
        const wrapper = mountComponent()
        expect(wrapper.text()).toContain('Upload Publication')
        expect(wrapper.find('.border-dashed').exists()).toBe(true)
    })

    it('emits pdfUpload event when file is chosen', async () => {
        const wrapper = mountComponent()
        const input = wrapper.find('input[type="file"]')
        expect(input.exists()).toBe(true)

        const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
        Object.defineProperty(input.element, 'files', { value: [file] })
        await input.trigger('change')

        expect(wrapper.emitted()).toHaveProperty('pdfUpload')
    })

    it('has a drop zone with dashed border', () => {
        const wrapper = mountComponent()
        const dropZone = wrapper.find('.border-dashed')
        expect(dropZone.exists()).toBe(true)
    })
})
