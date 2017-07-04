from typing import List

from webdnn.backend.code_generator.allocator import MemoryLayout
from webdnn.backend.code_generator.injectors.buffer_injector import BufferInjector
from webdnn.backend.code_generator.injectors.kernel_name_injector import KernelNameInjector
from webdnn.backend.webassembly.kernel import Kernel
from webdnn.graph.operators.elementwise_mul import ElementwiseMul

template_general = """
void %%FUNC_NAME%%(const int * %%META_BUFFER%%)
{
    const float *X0 = %%LOAD_BUFFER(elementwise_mul_X0)%%;
    const float *X1 = %%LOAD_BUFFER(elementwise_mul_X1)%%;
    float *Y = %%LOAD_BUFFER(elementwise_mul_Y)%%;
    const int N = %%LOAD_BUFFER(elementwise_mul_N)%%;
  
    for (int gid = 0; gid < N; gid += 1) {
        float result = X0[gid] * X1[gid];

        Y[gid] = result;
    }
}
"""


def elementwise_mul(op: ElementwiseMul, memory_layout: MemoryLayout) -> List[Kernel]:
    x0 = memory_layout[op.inputs["x0"]]
    x1 = memory_layout[op.inputs["x1"]]
    y = memory_layout[op.outputs["y"]]

    assert len(op.inputs) == 2, "[Webassembly] ElementwiseMul operator currently supported only 2 inputs."
    assert x0.variable.order == x1.variable.order == y.variable.order, \
        "[Webassembly] ElementwiseMul operator currently supported smae order inputs."
    assert x0.variable.shape == x1.variable.shape == y.variable.shape

    buffer_injector = BufferInjector()
    buffer_injector.register({
        "elementwise_mul_X0": x0,
        "elementwise_mul_X1": x1,
        "elementwise_mul_Y": y,
        "elementwise_mul_N": y.variable.size
    })

    name_injector = KernelNameInjector(op)

    source = template_general
    source = buffer_injector.inject(source)
    source = name_injector.inject(source)

    kernel = Kernel(
        {name_injector.name: source},
        name_injector.name,
        buffer_injector.buffer,
        buffer_injector.unresolved_value_list
    )

    return [kernel]